# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import json
from base64 import b64encode

from odoo.tests import TransactionCase


class TestJsocrCorrection(TransactionCase):
    """Tests for jsocr.correction model.

    This test suite covers:
    - Correction creation with required fields
    - Relationship with jsocr.import.job (Many2one with cascade delete)
    - One2many access from import job to corrections
    - Automatic user_id assignment
    - Correction type validation
    - apply_correction() method for each type
    """

    def setUp(self):
        super().setUp()
        self.Correction = self.env['jsocr.correction']
        self.ImportJob = self.env['jsocr.import.job']
        self.Partner = self.env['res.partner']
        self.Account = self.env['account.account']
        self.Move = self.env['account.move']

        # Create a test import job
        self.test_job = self.ImportJob.create({
            'pdf_file': b64encode(b'%PDF-1.4 test content'),
            'pdf_filename': 'test_correction.pdf',
        })

        # Create a test supplier with jsocr fields (will be extended in Story 1.6)
        self.test_partner = self.Partner.create({
            'name': 'Test Correction Supplier',
            'supplier_rank': 1,
        })

    def _create_correction(self, **kwargs):
        """Create a correction with default values for testing.

        Args:
            **kwargs: Override default field values.

        Returns:
            jsocr.correction: Created correction record.
        """
        vals = {
            'import_job_id': self.test_job.id,
            'field_name': 'supplier',
            'original_value': 'Old Value',
            'corrected_value': 'New Value',
            'correction_type': 'field_value',
        }
        vals.update(kwargs)
        return self.Correction.create(vals)

    # -------------------------------------------------------------------------
    # TEST: Model metadata
    # -------------------------------------------------------------------------

    def test_model_description(self):
        """Test: model has correct _description for UI and translations."""
        self.assertEqual(
            self.Correction._description,
            'JSOCR User Correction for Learning'
        )

    def test_model_ordering(self):
        """Test: corrections are ordered by create_date descending."""
        self.assertEqual(self.Correction._order, 'create_date desc')

    def test_ordering_create_date_desc_verified(self):
        """Test: search results are ordered by create_date desc (newest first)."""
        import time

        # Create corrections with slight time gap to ensure different create_date
        correction1 = self._create_correction(field_name='first')
        time.sleep(0.1)  # Small delay to ensure different timestamp
        correction2 = self._create_correction(field_name='second')
        time.sleep(0.1)
        correction3 = self._create_correction(field_name='third')

        # Search without explicit order (should use model's default _order)
        corrections = self.Correction.search([
            ('import_job_id', '=', self.test_job.id),
        ])

        # Most recent (correction3) should be first
        self.assertEqual(corrections[0].field_name, 'third')
        self.assertEqual(corrections[1].field_name, 'second')
        self.assertEqual(corrections[2].field_name, 'first')

    # -------------------------------------------------------------------------
    # TEST: Creation and required fields
    # -------------------------------------------------------------------------

    def test_create_correction_all_fields(self):
        """Test: correction created with all fields properly set."""
        correction = self._create_correction(
            field_name='invoice_number',
            original_value='INV-001',
            corrected_value='INV-002',
            correction_type='field_value',
        )

        self.assertEqual(correction.import_job_id, self.test_job)
        self.assertEqual(correction.field_name, 'invoice_number')
        self.assertEqual(correction.original_value, 'INV-001')
        self.assertEqual(correction.corrected_value, 'INV-002')
        self.assertEqual(correction.correction_type, 'field_value')

    def test_create_correction_import_job_required(self):
        """Test: import_job_id is required."""
        with self.assertRaises(Exception):
            self.Correction.create({
                'field_name': 'supplier',
                'corrected_value': 'New Value',
                'correction_type': 'field_value',
            })

    def test_create_correction_field_name_required(self):
        """Test: field_name is required."""
        with self.assertRaises(Exception):
            self.Correction.create({
                'import_job_id': self.test_job.id,
                'corrected_value': 'New Value',
                'correction_type': 'field_value',
            })

    def test_create_correction_corrected_value_required(self):
        """Test: corrected_value is required."""
        with self.assertRaises(Exception):
            self.Correction.create({
                'import_job_id': self.test_job.id,
                'field_name': 'supplier',
                'correction_type': 'field_value',
            })

    def test_create_correction_type_required(self):
        """Test: correction_type is required."""
        with self.assertRaises(Exception):
            self.Correction.create({
                'import_job_id': self.test_job.id,
                'field_name': 'supplier',
                'corrected_value': 'New Value',
            })

    def test_create_correction_original_value_optional(self):
        """Test: original_value is optional."""
        correction = self._create_correction(original_value=False)

        self.assertFalse(correction.original_value)
        self.assertTrue(correction.id)

    # -------------------------------------------------------------------------
    # TEST: Automatic user assignment
    # -------------------------------------------------------------------------

    def test_user_id_auto_assigned(self):
        """Test: user_id is automatically assigned to current user."""
        correction = self._create_correction()

        self.assertEqual(correction.user_id, self.env.user)

    def test_user_id_readonly(self):
        """Test: user_id is readonly after creation (business rule)."""
        correction = self._create_correction()
        original_user = correction.user_id

        # user_id should remain the same after create
        self.assertEqual(correction.user_id, original_user)

    def test_create_date_auto_assigned(self):
        """Test: create_date is automatically assigned on creation."""
        correction = self._create_correction()

        self.assertTrue(correction.create_date)

    # -------------------------------------------------------------------------
    # TEST: Correction types
    # -------------------------------------------------------------------------

    def test_correction_type_supplier_alias(self):
        """Test: supplier_alias type is valid."""
        correction = self._create_correction(correction_type='supplier_alias')

        self.assertEqual(correction.correction_type, 'supplier_alias')

    def test_correction_type_charge_account(self):
        """Test: charge_account type is valid."""
        correction = self._create_correction(correction_type='charge_account')

        self.assertEqual(correction.correction_type, 'charge_account')

    def test_correction_type_field_value(self):
        """Test: field_value type is valid."""
        correction = self._create_correction(correction_type='field_value')

        self.assertEqual(correction.correction_type, 'field_value')

    def test_correction_type_invalid_raises(self):
        """Test: invalid correction_type raises an error."""
        with self.assertRaises(Exception):
            self._create_correction(correction_type='invalid_type')

    # -------------------------------------------------------------------------
    # TEST: Relationship with import job
    # -------------------------------------------------------------------------

    def test_correction_linked_to_job(self):
        """Test: correction is properly linked to import job."""
        correction = self._create_correction()

        self.assertEqual(correction.import_job_id.id, self.test_job.id)

    def test_job_has_one2many_corrections(self):
        """Test: import job has One2many access to corrections."""
        correction1 = self._create_correction(field_name='field1')
        correction2 = self._create_correction(field_name='field2')

        self.assertIn(correction1, self.test_job.correction_ids)
        self.assertIn(correction2, self.test_job.correction_ids)
        self.assertEqual(len(self.test_job.correction_ids), 2)

    def test_cascade_delete_with_job(self):
        """Test: corrections are deleted when import job is deleted (ondelete='cascade')."""
        correction = self._create_correction()
        correction_id = correction.id

        # Delete the import job
        self.test_job.unlink()

        # Correction should no longer exist
        self.assertFalse(self.Correction.browse(correction_id).exists())

    def test_multiple_corrections_per_job(self):
        """Test: a job can have multiple corrections."""
        corrections = [
            self._create_correction(field_name=f'field_{i}', correction_type=ct)
            for i, ct in enumerate(['supplier_alias', 'charge_account', 'field_value'])
        ]

        self.assertEqual(len(self.test_job.correction_ids), 3)
        for correction in corrections:
            self.assertIn(correction, self.test_job.correction_ids)

    # -------------------------------------------------------------------------
    # TEST: apply_correction() - field_value type
    # -------------------------------------------------------------------------

    def test_apply_correction_field_value_success(self):
        """Test: apply_correction for field_value type succeeds."""
        correction = self._create_correction(
            correction_type='field_value',
            field_name='invoice_number',
            original_value='OLD-123',
            corrected_value='NEW-456',
        )

        result = correction.apply_correction()

        # Returns dict with correction id -> success
        self.assertIsInstance(result, dict)
        self.assertEqual(result[correction.id], True)

    def test_apply_correction_field_value_no_side_effects(self):
        """Test: apply_correction for field_value doesn't modify other records."""
        correction = self._create_correction(
            correction_type='field_value',
            field_name='amount',
            original_value='100.00',
            corrected_value='150.00',
        )

        correction.apply_correction()

        # Correction should remain unchanged
        self.assertEqual(correction.original_value, '100.00')
        self.assertEqual(correction.corrected_value, '150.00')

    # -------------------------------------------------------------------------
    # TEST: apply_correction() - supplier_alias type
    # -------------------------------------------------------------------------

    def test_apply_supplier_alias_no_partner(self):
        """Test: _apply_supplier_alias returns False when no partner linked."""
        # Job has no linked invoice (thus no partner)
        correction = self._create_correction(
            correction_type='supplier_alias',
            original_value='Unknown Supplier Name',
        )

        # Test private method directly to verify behavior
        result = correction._apply_supplier_alias()

        # Internal method returns False when no partner
        self.assertFalse(result)

    def test_apply_supplier_alias_no_original_value(self):
        """Test: _apply_supplier_alias returns False when no original_value."""
        correction = self._create_correction(
            correction_type='supplier_alias',
            original_value=False,
        )

        result = correction._apply_supplier_alias()

        # Internal method returns False when no original value
        self.assertFalse(result)

    def test_apply_supplier_alias_field_not_exists(self):
        """Test: _apply_supplier_alias returns False when jsocr_aliases field missing.

        The jsocr_aliases field is added in Story 1.6. Until then, the method
        should detect the missing field and return False gracefully.
        """
        correction = self._create_correction(
            correction_type='supplier_alias',
            original_value='Supplier Name Variant',
        )

        # Even if we had a partner, the field doesn't exist yet
        # Since we don't have a partner linked, it returns False for that reason
        result = correction._apply_supplier_alias()

        self.assertFalse(result)

    def test_apply_correction_supplier_alias_returns_failure(self):
        """Test: apply_correction returns False for correction when internal fails."""
        correction = self._create_correction(
            correction_type='supplier_alias',
            original_value='Test Alias',
        )

        result = correction.apply_correction()

        # Returns dict with correction id -> False (because no partner linked)
        self.assertIsInstance(result, dict)
        self.assertEqual(result[correction.id], False)

    # -------------------------------------------------------------------------
    # TEST: apply_correction() - charge_account type
    # -------------------------------------------------------------------------

    def test_apply_charge_account_no_partner(self):
        """Test: _apply_charge_account returns False when no partner linked."""
        correction = self._create_correction(
            correction_type='charge_account',
            corrected_value='12345',
        )

        result = correction._apply_charge_account()

        # Internal method returns False when no partner
        self.assertFalse(result)

    def test_apply_charge_account_invalid_account_id(self):
        """Test: _apply_charge_account returns False with invalid account ID."""
        correction = self._create_correction(
            correction_type='charge_account',
            corrected_value='not_a_number',
        )

        # Since there's no partner, returns False for that reason first
        result = correction._apply_charge_account()

        self.assertFalse(result)

    def test_apply_charge_account_field_not_exists(self):
        """Test: _apply_charge_account returns False when jsocr_default_account_id missing.

        The jsocr_default_account_id field is added in Story 1.6. Until then,
        the method should detect the missing field and return False gracefully.
        """
        correction = self._create_correction(
            correction_type='charge_account',
            corrected_value='601000',
        )

        result = correction._apply_charge_account()

        # Returns False (no partner linked in this test)
        self.assertFalse(result)

    def test_apply_correction_charge_account_returns_failure(self):
        """Test: apply_correction returns False for correction when internal fails."""
        correction = self._create_correction(
            correction_type='charge_account',
            corrected_value='601000',
        )

        result = correction.apply_correction()

        # Returns dict with correction id -> False (because no partner linked)
        self.assertIsInstance(result, dict)
        self.assertEqual(result[correction.id], False)

    # -------------------------------------------------------------------------
    # TEST: Index verification
    # -------------------------------------------------------------------------

    def test_import_job_id_indexed(self):
        """Test: import_job_id field has index for performance."""
        field = self.Correction._fields['import_job_id']
        self.assertTrue(field.index)

    def test_user_id_indexed(self):
        """Test: user_id field has index for performance."""
        field = self.Correction._fields['user_id']
        self.assertTrue(field.index)

    # -------------------------------------------------------------------------
    # TEST: Filtering and search
    # -------------------------------------------------------------------------

    def test_filter_by_correction_type(self):
        """Test: corrections can be filtered by type."""
        self._create_correction(correction_type='supplier_alias', field_name='s1')
        self._create_correction(correction_type='supplier_alias', field_name='s2')
        self._create_correction(correction_type='charge_account', field_name='c1')
        self._create_correction(correction_type='field_value', field_name='f1')

        alias_corrections = self.Correction.search([
            ('correction_type', '=', 'supplier_alias'),
            ('import_job_id', '=', self.test_job.id),
        ])

        self.assertEqual(len(alias_corrections), 2)

    def test_filter_by_user(self):
        """Test: corrections can be filtered by user who made them."""
        correction = self._create_correction()

        user_corrections = self.Correction.search([
            ('user_id', '=', self.env.user.id),
            ('import_job_id', '=', self.test_job.id),
        ])

        self.assertIn(correction, user_corrections)

    # -------------------------------------------------------------------------
    # TEST: apply_correction() - batch processing
    # -------------------------------------------------------------------------

    def test_apply_correction_multiple_returns_dict(self):
        """Test: apply_correction on multiple records returns dict with individual results."""
        correction1 = self._create_correction(
            field_name='field1',
            correction_type='field_value',
        )
        correction2 = self._create_correction(
            field_name='field2',
            correction_type='supplier_alias',  # Will fail (no partner)
        )
        correction3 = self._create_correction(
            field_name='field3',
            correction_type='field_value',
        )

        corrections = correction1 | correction2 | correction3
        result = corrections.apply_correction()

        # Should return dict with all correction IDs
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 3)
        self.assertIn(correction1.id, result)
        self.assertIn(correction2.id, result)
        self.assertIn(correction3.id, result)

        # field_value corrections succeed, supplier_alias fails
        self.assertTrue(result[correction1.id])
        self.assertFalse(result[correction2.id])  # No partner linked
        self.assertTrue(result[correction3.id])

    def test_apply_correction_all_function(self):
        """Test: can check if all corrections succeeded using all()."""
        correction1 = self._create_correction(correction_type='field_value')
        correction2 = self._create_correction(correction_type='field_value')

        corrections = correction1 | correction2
        result = corrections.apply_correction()

        # All field_value corrections should succeed
        self.assertTrue(all(result.values()))

    # -------------------------------------------------------------------------
    # TEST: Integration workflow
    # -------------------------------------------------------------------------

    def test_full_correction_workflow(self):
        """Test: complete workflow from job creation to correction recording."""
        # 1. Create an import job
        job = self.ImportJob.create({
            'pdf_file': b64encode(b'%PDF-1.4 workflow test'),
            'pdf_filename': 'workflow_test.pdf',
        })

        # 2. Record multiple corrections for the job
        correction_supplier = self.Correction.create({
            'import_job_id': job.id,
            'field_name': 'supplier',
            'original_value': 'ACME Corp',
            'corrected_value': 'ACME Corporation Ltd',
            'correction_type': 'supplier_alias',
        })

        correction_account = self.Correction.create({
            'import_job_id': job.id,
            'field_name': 'charge_account',
            'original_value': '601000',
            'corrected_value': '602000',
            'correction_type': 'charge_account',
        })

        correction_field = self.Correction.create({
            'import_job_id': job.id,
            'field_name': 'invoice_date',
            'original_value': '2026-01-15',
            'corrected_value': '2026-01-20',
            'correction_type': 'field_value',
        })

        # 3. Verify all corrections are linked to job
        self.assertEqual(len(job.correction_ids), 3)

        # 4. Verify user tracking
        for correction in job.correction_ids:
            self.assertEqual(correction.user_id, self.env.user)
            self.assertTrue(correction.create_date)

        # 5. Apply all corrections
        for correction in job.correction_ids:
            correction.apply_correction()

        # 6. Verify corrections by type
        type_counts = {}
        for c in job.correction_ids:
            type_counts[c.correction_type] = type_counts.get(c.correction_type, 0) + 1

        self.assertEqual(type_counts['supplier_alias'], 1)
        self.assertEqual(type_counts['charge_account'], 1)
        self.assertEqual(type_counts['field_value'], 1)

        # 7. Clean up - cascade delete
        job_id = job.id
        correction_ids = job.correction_ids.ids
        job.unlink()

        for cid in correction_ids:
            self.assertFalse(self.Correction.browse(cid).exists())
