# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import json
from base64 import b64encode

from odoo.tests import TransactionCase


class TestAccountMoveExtension(TransactionCase):
    """Tests for account.move JSOCR extension.

    This test suite covers:
    - JSOCR fields exist on account.move
    - get_field_confidence() method
    - get_field_value() method
    - get_all_confidences() method
    - set_field_confidence() method
    - get_low_confidence_fields() method
    - is_jsocr_invoice() method
    """

    def setUp(self):
        super().setUp()
        self.Move = self.env['account.move']
        self.ImportJob = self.env['jsocr.import.job']
        self.Partner = self.env['res.partner']

        # Create a test supplier
        self.test_partner = self.Partner.create({
            'name': 'Test Invoice Partner',
            'supplier_rank': 1,
        })

        # Create a test invoice
        self.test_invoice = self.Move.create({
            'move_type': 'in_invoice',
            'partner_id': self.test_partner.id,
        })

        # Create a test import job
        self.test_job = self.ImportJob.create({
            'pdf_file': b64encode(b'%PDF-1.4 test'),
            'pdf_filename': 'test.pdf',
        })

    # -------------------------------------------------------------------------
    # TEST: JSOCR fields exist
    # -------------------------------------------------------------------------

    def test_jsocr_import_job_id_field_exists(self):
        """Test: jsocr_import_job_id field exists on account.move."""
        self.assertIn('jsocr_import_job_id', self.Move._fields)

    def test_jsocr_confidence_data_field_exists(self):
        """Test: jsocr_confidence_data field exists on account.move."""
        self.assertIn('jsocr_confidence_data', self.Move._fields)

    def test_jsocr_source_pdf_field_exists(self):
        """Test: jsocr_source_pdf field exists on account.move."""
        self.assertIn('jsocr_source_pdf', self.Move._fields)

    def test_jsocr_source_pdf_filename_field_exists(self):
        """Test: jsocr_source_pdf_filename field exists on account.move."""
        self.assertIn('jsocr_source_pdf_filename', self.Move._fields)

    def test_jsocr_import_job_id_indexed(self):
        """Test: jsocr_import_job_id field is indexed."""
        field = self.Move._fields['jsocr_import_job_id']
        self.assertTrue(field.index)

    # -------------------------------------------------------------------------
    # TEST: get_field_confidence() method
    # -------------------------------------------------------------------------

    def test_get_field_confidence_returns_value(self):
        """Test: get_field_confidence returns confidence score."""
        self.test_invoice.jsocr_confidence_data = json.dumps({
            'supplier': {'value': 'Test Corp', 'confidence': 95},
            'date': {'value': '2026-01-15', 'confidence': 88},
        })

        result = self.test_invoice.get_field_confidence('supplier')

        self.assertEqual(result, 95)

    def test_get_field_confidence_different_fields(self):
        """Test: get_field_confidence returns correct value per field."""
        self.test_invoice.jsocr_confidence_data = json.dumps({
            'supplier': {'value': 'Test', 'confidence': 95},
            'date': {'value': '2026-01-15', 'confidence': 88},
            'total': {'value': 1250.00, 'confidence': 72},
        })

        self.assertEqual(self.test_invoice.get_field_confidence('supplier'), 95)
        self.assertEqual(self.test_invoice.get_field_confidence('date'), 88)
        self.assertEqual(self.test_invoice.get_field_confidence('total'), 72)

    def test_get_field_confidence_not_found(self):
        """Test: get_field_confidence returns None for unknown field."""
        self.test_invoice.jsocr_confidence_data = json.dumps({
            'supplier': {'value': 'Test', 'confidence': 95},
        })

        result = self.test_invoice.get_field_confidence('unknown_field')

        self.assertIsNone(result)

    def test_get_field_confidence_no_data(self):
        """Test: get_field_confidence returns None when no confidence data."""
        result = self.test_invoice.get_field_confidence('supplier')

        self.assertIsNone(result)

    def test_get_field_confidence_invalid_json(self):
        """Test: get_field_confidence handles invalid JSON gracefully."""
        self.test_invoice.jsocr_confidence_data = 'not valid json'

        result = self.test_invoice.get_field_confidence('supplier')

        self.assertIsNone(result)

    def test_get_field_confidence_none_field_name(self):
        """Test: get_field_confidence returns None for None field name."""
        self.test_invoice.jsocr_confidence_data = json.dumps({
            'supplier': {'value': 'Test', 'confidence': 95},
        })

        result = self.test_invoice.get_field_confidence(None)

        self.assertIsNone(result)

    def test_get_field_confidence_missing_confidence_key(self):
        """Test: get_field_confidence returns None when confidence key missing."""
        self.test_invoice.jsocr_confidence_data = json.dumps({
            'supplier': {'value': 'Test'},  # no confidence key
        })

        result = self.test_invoice.get_field_confidence('supplier')

        self.assertIsNone(result)

    # -------------------------------------------------------------------------
    # TEST: get_field_value() method
    # -------------------------------------------------------------------------

    def test_get_field_value_returns_value(self):
        """Test: get_field_value returns extracted value."""
        self.test_invoice.jsocr_confidence_data = json.dumps({
            'supplier': {'value': 'Test Corp', 'confidence': 95},
        })

        result = self.test_invoice.get_field_value('supplier')

        self.assertEqual(result, 'Test Corp')

    def test_get_field_value_numeric(self):
        """Test: get_field_value returns numeric values correctly."""
        self.test_invoice.jsocr_confidence_data = json.dumps({
            'total': {'value': 1250.50, 'confidence': 90},
        })

        result = self.test_invoice.get_field_value('total')

        self.assertEqual(result, 1250.50)

    def test_get_field_value_not_found(self):
        """Test: get_field_value returns None for unknown field."""
        self.test_invoice.jsocr_confidence_data = json.dumps({
            'supplier': {'value': 'Test', 'confidence': 95},
        })

        result = self.test_invoice.get_field_value('unknown')

        self.assertIsNone(result)

    def test_get_field_value_no_data(self):
        """Test: get_field_value returns None when no confidence data."""
        result = self.test_invoice.get_field_value('supplier')

        self.assertIsNone(result)

    # -------------------------------------------------------------------------
    # TEST: get_all_confidences() method
    # -------------------------------------------------------------------------

    def test_get_all_confidences_returns_dict(self):
        """Test: get_all_confidences returns dictionary of all confidences."""
        self.test_invoice.jsocr_confidence_data = json.dumps({
            'supplier': {'value': 'Test', 'confidence': 95},
            'date': {'value': '2026-01-15', 'confidence': 88},
            'total': {'value': 1250, 'confidence': 72},
        })

        result = self.test_invoice.get_all_confidences()

        self.assertEqual(result, {
            'supplier': 95,
            'date': 88,
            'total': 72,
        })

    def test_get_all_confidences_empty(self):
        """Test: get_all_confidences returns empty dict when no data."""
        result = self.test_invoice.get_all_confidences()

        self.assertEqual(result, {})

    def test_get_all_confidences_skips_invalid(self):
        """Test: get_all_confidences skips fields with invalid confidence."""
        self.test_invoice.jsocr_confidence_data = json.dumps({
            'valid': {'value': 'Test', 'confidence': 90},
            'invalid': {'value': 'Test'},  # missing confidence
            'also_invalid': 'not a dict',
        })

        result = self.test_invoice.get_all_confidences()

        self.assertEqual(result, {'valid': 90})

    # -------------------------------------------------------------------------
    # TEST: set_field_confidence() method
    # -------------------------------------------------------------------------

    def test_set_field_confidence_new_field(self):
        """Test: set_field_confidence sets value for new field."""
        result = self.test_invoice.set_field_confidence('supplier', 'Test Corp', 95)

        self.assertTrue(result)
        self.assertEqual(self.test_invoice.get_field_confidence('supplier'), 95)
        self.assertEqual(self.test_invoice.get_field_value('supplier'), 'Test Corp')

    def test_set_field_confidence_update_field(self):
        """Test: set_field_confidence updates existing field."""
        self.test_invoice.set_field_confidence('supplier', 'Old', 80)
        self.test_invoice.set_field_confidence('supplier', 'New', 95)

        self.assertEqual(self.test_invoice.get_field_confidence('supplier'), 95)
        self.assertEqual(self.test_invoice.get_field_value('supplier'), 'New')

    def test_set_field_confidence_multiple_fields(self):
        """Test: set_field_confidence can set multiple fields."""
        self.test_invoice.set_field_confidence('supplier', 'Test', 95)
        self.test_invoice.set_field_confidence('date', '2026-01-15', 88)
        self.test_invoice.set_field_confidence('total', 1250, 72)

        all_conf = self.test_invoice.get_all_confidences()
        self.assertEqual(len(all_conf), 3)

    def test_set_field_confidence_invalid_range_high(self):
        """Test: set_field_confidence rejects confidence > 100."""
        result = self.test_invoice.set_field_confidence('field', 'value', 101)

        self.assertFalse(result)

    def test_set_field_confidence_invalid_range_low(self):
        """Test: set_field_confidence rejects confidence < 0."""
        result = self.test_invoice.set_field_confidence('field', 'value', -1)

        self.assertFalse(result)

    def test_set_field_confidence_empty_field_name(self):
        """Test: set_field_confidence rejects empty field name."""
        result = self.test_invoice.set_field_confidence('', 'value', 90)

        self.assertFalse(result)

    def test_set_field_confidence_boundary_values(self):
        """Test: set_field_confidence accepts boundary values 0 and 100."""
        self.test_invoice.set_field_confidence('low', 'val', 0)
        self.test_invoice.set_field_confidence('high', 'val', 100)

        self.assertEqual(self.test_invoice.get_field_confidence('low'), 0)
        self.assertEqual(self.test_invoice.get_field_confidence('high'), 100)

    # -------------------------------------------------------------------------
    # TEST: get_low_confidence_fields() method
    # -------------------------------------------------------------------------

    def test_get_low_confidence_fields_default_threshold(self):
        """Test: get_low_confidence_fields uses default threshold of 80."""
        self.test_invoice.jsocr_confidence_data = json.dumps({
            'high': {'value': 'v', 'confidence': 95},
            'low': {'value': 'v', 'confidence': 75},
            'very_low': {'value': 'v', 'confidence': 50},
        })

        result = self.test_invoice.get_low_confidence_fields()

        self.assertEqual(len(result), 2)
        field_names = [f[0] for f in result]
        self.assertIn('low', field_names)
        self.assertIn('very_low', field_names)
        self.assertNotIn('high', field_names)

    def test_get_low_confidence_fields_custom_threshold(self):
        """Test: get_low_confidence_fields uses custom threshold."""
        self.test_invoice.jsocr_confidence_data = json.dumps({
            'high': {'value': 'v', 'confidence': 95},
            'medium': {'value': 'v', 'confidence': 85},
            'low': {'value': 'v', 'confidence': 75},
        })

        result = self.test_invoice.get_low_confidence_fields(threshold=90)

        self.assertEqual(len(result), 2)
        field_names = [f[0] for f in result]
        self.assertIn('medium', field_names)
        self.assertIn('low', field_names)

    def test_get_low_confidence_fields_empty(self):
        """Test: get_low_confidence_fields returns empty when all high."""
        self.test_invoice.jsocr_confidence_data = json.dumps({
            'all_high': {'value': 'v', 'confidence': 95},
        })

        result = self.test_invoice.get_low_confidence_fields()

        self.assertEqual(result, [])

    def test_get_low_confidence_fields_no_data(self):
        """Test: get_low_confidence_fields returns empty when no data."""
        result = self.test_invoice.get_low_confidence_fields()

        self.assertEqual(result, [])

    # -------------------------------------------------------------------------
    # TEST: is_jsocr_invoice() method
    # -------------------------------------------------------------------------

    def test_is_jsocr_invoice_true(self):
        """Test: is_jsocr_invoice returns True when job linked."""
        self.test_invoice.jsocr_import_job_id = self.test_job.id

        result = self.test_invoice.is_jsocr_invoice()

        self.assertTrue(result)

    def test_is_jsocr_invoice_false(self):
        """Test: is_jsocr_invoice returns False when no job linked."""
        result = self.test_invoice.is_jsocr_invoice()

        self.assertFalse(result)

    # -------------------------------------------------------------------------
    # TEST: jsocr_source_pdf field
    # -------------------------------------------------------------------------

    def test_jsocr_source_pdf_can_be_set(self):
        """Test: jsocr_source_pdf can store binary data."""
        pdf_content = b64encode(b'%PDF-1.4 test content')
        self.test_invoice.jsocr_source_pdf = pdf_content
        self.test_invoice.jsocr_source_pdf_filename = 'test.pdf'

        self.assertEqual(self.test_invoice.jsocr_source_pdf, pdf_content)
        self.assertEqual(self.test_invoice.jsocr_source_pdf_filename, 'test.pdf')

    # -------------------------------------------------------------------------
    # TEST: Relationship with import job
    # -------------------------------------------------------------------------

    def test_link_to_import_job(self):
        """Test: invoice can be linked to import job."""
        self.test_invoice.jsocr_import_job_id = self.test_job.id

        self.assertEqual(self.test_invoice.jsocr_import_job_id, self.test_job)

    def test_import_job_ondelete_set_null(self):
        """Test: deleting import job sets invoice link to null."""
        self.test_invoice.jsocr_import_job_id = self.test_job.id
        self.test_job.unlink()

        self.assertFalse(self.test_invoice.jsocr_import_job_id)

    # -------------------------------------------------------------------------
    # TEST: Integration
    # -------------------------------------------------------------------------

    def test_full_confidence_workflow(self):
        """Test: complete confidence data workflow."""
        # Link to import job
        self.test_invoice.jsocr_import_job_id = self.test_job.id

        # Set confidence data
        self.test_invoice.set_field_confidence('supplier', 'ACME Corp', 95)
        self.test_invoice.set_field_confidence('date', '2026-01-15', 88)
        self.test_invoice.set_field_confidence('total', 1250.50, 72)
        self.test_invoice.set_field_confidence('invoice_number', 'INV-001', 60)

        # Verify it's a JSOCR invoice
        self.assertTrue(self.test_invoice.is_jsocr_invoice())

        # Get all confidences
        all_conf = self.test_invoice.get_all_confidences()
        self.assertEqual(len(all_conf), 4)

        # Get low confidence fields (< 80)
        low_conf = self.test_invoice.get_low_confidence_fields()
        self.assertEqual(len(low_conf), 2)  # total=72, invoice_number=60

        # Get specific values
        self.assertEqual(self.test_invoice.get_field_value('supplier'), 'ACME Corp')
        self.assertEqual(self.test_invoice.get_field_confidence('supplier'), 95)
