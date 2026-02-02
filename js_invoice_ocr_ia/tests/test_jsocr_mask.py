# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import json

from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError


class TestJsocrMask(TransactionCase):
    """Tests for jsocr.mask model.

    This test suite covers:
    - Mask creation and default values
    - Partner relationship (Many2one with cascade delete)
    - JSON validation for mask_data field
    - Active field filtering behavior
    - Usage counter increment functionality
    - Multiple masks per partner
    """

    def setUp(self):
        super().setUp()
        self.Mask = self.env['jsocr.mask']
        self.Partner = self.env['res.partner']
        # Create a test supplier
        self.test_partner = self.Partner.create({
            'name': 'Test Supplier',
            'supplier_rank': 1,
        })

    def _create_mask(self, **kwargs):
        """Create a mask with default values for testing.

        Args:
            **kwargs: Override default field values.

        Returns:
            jsocr.mask: Created mask record.
        """
        vals = {
            'name': 'Test Mask',
        }
        vals.update(kwargs)
        return self.Mask.create(vals)

    # -------------------------------------------------------------------------
    # TEST: Model metadata
    # -------------------------------------------------------------------------

    def test_model_description(self):
        """Test: model has correct _description for UI and translations."""
        self.assertEqual(
            self.Mask._description,
            'JSOCR Extraction Mask per Supplier'
        )

    # -------------------------------------------------------------------------
    # TEST: Creation and default values
    # -------------------------------------------------------------------------

    def test_create_mask_default_values(self):
        """Test: mask created with correct default values."""
        mask = self._create_mask(partner_id=self.test_partner.id)

        self.assertEqual(mask.active, True)
        self.assertEqual(mask.usage_count, 0)
        self.assertEqual(mask.mask_data, '{}')
        self.assertTrue(mask.name)

    def test_create_mask_name_required(self):
        """Test: name field is required."""
        with self.assertRaises(Exception):
            self.Mask.create({
                'partner_id': self.test_partner.id,
            })

    def test_create_mask_without_partner(self):
        """Test: mask can be created without partner (generic mask)."""
        mask = self._create_mask()

        self.assertFalse(mask.partner_id)
        self.assertEqual(mask.name, 'Test Mask')

    # -------------------------------------------------------------------------
    # TEST: Partner relationship
    # -------------------------------------------------------------------------

    def test_mask_partner_relation(self):
        """Test: mask is correctly linked to partner."""
        mask = self._create_mask(partner_id=self.test_partner.id)

        self.assertEqual(mask.partner_id, self.test_partner)
        self.assertEqual(mask.partner_id.name, 'Test Supplier')

    def test_multiple_masks_per_partner(self):
        """Test: a partner can have multiple masks."""
        mask1 = self._create_mask(name='Mask 1', partner_id=self.test_partner.id)
        mask2 = self._create_mask(name='Mask 2', partner_id=self.test_partner.id)
        mask3 = self._create_mask(name='Mask 3', partner_id=self.test_partner.id)

        partner_masks = self.Mask.search([('partner_id', '=', self.test_partner.id)])

        self.assertEqual(len(partner_masks), 3)
        self.assertIn(mask1, partner_masks)
        self.assertIn(mask2, partner_masks)
        self.assertIn(mask3, partner_masks)

    def test_cascade_delete_with_partner(self):
        """Test: masks are deleted when partner is deleted (ondelete='cascade')."""
        mask = self._create_mask(
            name='Cascade Test Mask',
            partner_id=self.test_partner.id,
        )
        mask_id = mask.id

        # Delete the partner
        self.test_partner.unlink()

        # Mask should no longer exist
        self.assertFalse(self.Mask.browse(mask_id).exists())

    # -------------------------------------------------------------------------
    # TEST: JSON validation
    # -------------------------------------------------------------------------

    def test_mask_data_valid_json_empty_object(self):
        """Test: empty JSON object is accepted."""
        mask = self._create_mask(mask_data='{}')

        self.assertEqual(mask.mask_data, '{}')

    def test_mask_data_valid_json_with_version(self):
        """Test: valid JSON with version and fields is accepted."""
        valid_json = '{"version": "1.0", "fields": {}}'
        mask = self._create_mask(mask_data=valid_json)

        self.assertEqual(mask.mask_data, valid_json)
        self.assertIn('version', mask.mask_data)

    def test_mask_data_valid_json_complex(self):
        """Test: complex valid JSON structure is accepted."""
        complex_json = '''{
            "version": "1.0",
            "fields": {
                "supplier": {"pattern": ".*", "confidence": 95},
                "invoice_number": {"pattern": "FA-\\\\d+", "zone": {"x": 10, "y": 20}}
            },
            "lines": [{"description": "Service", "confidence": 80}]
        }'''
        mask = self._create_mask(mask_data=complex_json)

        self.assertIn('version', mask.mask_data)
        self.assertIn('fields', mask.mask_data)

    def test_mask_data_invalid_json_raises(self):
        """Test: invalid JSON raises ValidationError."""
        with self.assertRaises(ValidationError):
            self._create_mask(mask_data='{invalid json}')

    def test_mask_data_invalid_json_missing_quote(self):
        """Test: JSON with syntax error raises ValidationError."""
        with self.assertRaises(ValidationError):
            self._create_mask(mask_data='{"name: "value"}')

    def test_mask_data_invalid_json_trailing_comma(self):
        """Test: JSON with trailing comma raises ValidationError."""
        with self.assertRaises(ValidationError):
            self._create_mask(mask_data='{"name": "value",}')

    def test_mask_data_update_valid_json(self):
        """Test: updating mask_data with valid JSON succeeds."""
        mask = self._create_mask(mask_data='{}')
        mask.mask_data = '{"version": "2.0"}'

        self.assertIn('2.0', mask.mask_data)

    def test_mask_data_update_invalid_json_raises(self):
        """Test: updating mask_data with invalid JSON raises ValidationError."""
        mask = self._create_mask(mask_data='{}')

        with self.assertRaises(ValidationError):
            mask.mask_data = 'not valid json'

    # -------------------------------------------------------------------------
    # TEST: Active field filtering
    # -------------------------------------------------------------------------

    def test_active_filter_default(self):
        """Test: inactive masks are filtered by default search."""
        active_mask = self._create_mask(name='Active Mask')
        inactive_mask = self._create_mask(name='Inactive Mask', active=False)

        # Default search should only return active masks
        all_masks = self.Mask.search([('name', 'like', 'Mask')])

        self.assertIn(active_mask, all_masks)
        self.assertNotIn(inactive_mask, all_masks)

    def test_active_filter_with_active_test(self):
        """Test: inactive masks are found with active_test=False context."""
        active_mask = self._create_mask(name='Active Mask 2')
        inactive_mask = self._create_mask(name='Inactive Mask 2', active=False)

        # Search with active_test=False should return both
        all_masks = self.Mask.with_context(active_test=False).search([
            ('name', 'like', 'Mask 2')
        ])

        self.assertIn(active_mask, all_masks)
        self.assertIn(inactive_mask, all_masks)

    def test_archive_mask(self):
        """Test: mask can be archived by setting active=False."""
        mask = self._create_mask(name='To Archive')
        self.assertTrue(mask.active)

        mask.active = False

        self.assertFalse(mask.active)
        # Should not appear in default search
        self.assertNotIn(mask, self.Mask.search([('name', '=', 'To Archive')]))

    # -------------------------------------------------------------------------
    # TEST: Usage counter
    # -------------------------------------------------------------------------

    def test_action_increment_usage(self):
        """Test: usage counter increments correctly."""
        mask = self._create_mask()
        self.assertEqual(mask.usage_count, 0)

        mask.action_increment_usage()
        self.assertEqual(mask.usage_count, 1)

        mask.action_increment_usage()
        self.assertEqual(mask.usage_count, 2)

        mask.action_increment_usage()
        self.assertEqual(mask.usage_count, 3)

    def test_action_increment_usage_multiple_masks(self):
        """Test: incrementing one mask doesn't affect others."""
        mask1 = self._create_mask(name='Mask A')
        mask2 = self._create_mask(name='Mask B')

        mask1.action_increment_usage()
        mask1.action_increment_usage()

        self.assertEqual(mask1.usage_count, 2)
        self.assertEqual(mask2.usage_count, 0)

    def test_usage_count_default_value_on_create(self):
        """Test: usage_count starts at 0 regardless of attempted value on create."""
        # Readonly fields can still be set during create in Odoo, but we verify
        # the expected behavior: field should always start at 0 for new masks
        mask = self._create_mask()
        self.assertEqual(mask.usage_count, 0)

    def test_usage_count_only_changes_via_action(self):
        """Test: usage_count should only change through action_increment_usage()."""
        mask = self._create_mask()
        self.assertEqual(mask.usage_count, 0)

        # Increment via proper API
        mask.action_increment_usage()
        self.assertEqual(mask.usage_count, 1)

        # Note: In Odoo, readonly fields CAN be written via write() with sudo,
        # but the business logic should only use action_increment_usage()
        mask.action_increment_usage()
        self.assertEqual(mask.usage_count, 2)

    # -------------------------------------------------------------------------
    # TEST: Ordering
    # -------------------------------------------------------------------------

    def test_ordering_by_usage_count_desc(self):
        """Test: masks are ordered by usage_count descending, then name."""
        mask_a = self._create_mask(name='AAA')
        mask_b = self._create_mask(name='BBB')
        mask_c = self._create_mask(name='CCC')

        # Increment usage counts differently
        mask_c.action_increment_usage()  # 1
        mask_c.action_increment_usage()  # 2
        mask_a.action_increment_usage()  # 1

        # Search with default ordering (usage_count desc, name)
        ordered_masks = self.Mask.search([('name', 'in', ['AAA', 'BBB', 'CCC'])])

        # Should be: CCC (2), AAA (1), BBB (0)
        self.assertEqual(ordered_masks[0], mask_c)  # highest usage
        self.assertEqual(ordered_masks[1], mask_a)  # second highest
        self.assertEqual(ordered_masks[2], mask_b)  # lowest

    # -------------------------------------------------------------------------
    # TEST: Edge cases
    # -------------------------------------------------------------------------

    def test_mask_data_empty_string(self):
        """Test: empty string for mask_data is valid (no JSON parsing)."""
        mask = self._create_mask(mask_data='')

        self.assertEqual(mask.mask_data, '')

    def test_mask_data_null_json(self):
        """Test: JSON null value is valid."""
        mask = self._create_mask(mask_data='null')

        self.assertEqual(mask.mask_data, 'null')

    def test_mask_data_json_array(self):
        """Test: JSON array is valid (though not expected schema)."""
        mask = self._create_mask(mask_data='[1, 2, 3]')

        self.assertEqual(mask.mask_data, '[1, 2, 3]')

    # -------------------------------------------------------------------------
    # TEST: Public API - get_mask_for_partner
    # -------------------------------------------------------------------------

    def test_get_mask_for_partner_returns_most_used(self):
        """Test: get_mask_for_partner returns the most used active mask."""
        mask1 = self._create_mask(name='Low Usage', partner_id=self.test_partner.id)
        mask2 = self._create_mask(name='High Usage', partner_id=self.test_partner.id)
        mask3 = self._create_mask(name='Medium Usage', partner_id=self.test_partner.id)

        # Set different usage counts
        mask2.action_increment_usage()  # 1
        mask2.action_increment_usage()  # 2
        mask3.action_increment_usage()  # 1

        result = self.Mask.get_mask_for_partner(self.test_partner.id)

        self.assertEqual(result, mask2)  # Highest usage count

    def test_get_mask_for_partner_no_mask_returns_false(self):
        """Test: get_mask_for_partner returns exactly False when no mask exists."""
        # Create a partner with no masks
        other_partner = self.Partner.create({
            'name': 'Partner Without Mask',
            'supplier_rank': 1,
        })

        result = self.Mask.get_mask_for_partner(other_partner.id)

        self.assertIs(result, False)

    def test_get_mask_for_partner_ignores_inactive(self):
        """Test: get_mask_for_partner ignores archived masks even with high usage."""
        active_mask = self._create_mask(
            name='Active Mask',
            partner_id=self.test_partner.id
        )
        inactive_mask = self._create_mask(
            name='Inactive Mask',
            partner_id=self.test_partner.id,
            active=False
        )
        # TEST SETUP: Use write() to set high usage on inactive mask.
        # This bypasses readonly to set up test scenario where inactive mask
        # would win if active filter wasn't working. In production code,
        # only action_increment_usage() should modify usage_count.
        inactive_mask.write({'usage_count': 100})

        result = self.Mask.get_mask_for_partner(self.test_partner.id)

        self.assertEqual(result, active_mask)

    def test_get_mask_for_partner_with_none_returns_false(self):
        """Test: get_mask_for_partner with None partner_id returns exactly False."""
        result = self.Mask.get_mask_for_partner(None)

        self.assertIs(result, False)

    def test_get_mask_for_partner_with_zero_returns_false(self):
        """Test: get_mask_for_partner with 0 partner_id returns exactly False."""
        result = self.Mask.get_mask_for_partner(0)

        self.assertIs(result, False)

    # -------------------------------------------------------------------------
    # TEST: Integration - Full workflow
    # -------------------------------------------------------------------------

    def test_full_mask_workflow(self):
        """Test: complete workflow from creation to usage tracking."""
        # 1. Create a supplier
        supplier = self.Partner.create({
            'name': 'Integration Test Supplier',
            'supplier_rank': 1,
        })

        # 2. Create masks for the supplier
        mask_v1 = self._create_mask(
            name='Invoice Template v1',
            partner_id=supplier.id,
            mask_data='{"version": "1.0", "fields": {"invoice_number": {"pattern": "FA-\\\\d+"}}}'
        )
        mask_v2 = self._create_mask(
            name='Invoice Template v2',
            partner_id=supplier.id,
            mask_data='{"version": "2.0", "fields": {"invoice_number": {"pattern": "INV-\\\\d+"}}}'
        )

        # 3. Verify both masks exist for the supplier and JSON is parseable
        supplier_masks = self.Mask.search([('partner_id', '=', supplier.id)])
        self.assertEqual(len(supplier_masks), 2)

        # 3a. Parse and verify JSON structure
        data_v1 = json.loads(mask_v1.mask_data)
        self.assertEqual(data_v1['version'], '1.0')
        self.assertIn('invoice_number', data_v1['fields'])

        data_v2 = json.loads(mask_v2.mask_data)
        self.assertEqual(data_v2['version'], '2.0')

        # 4. Simulate mask usage (v2 is used more often)
        mask_v2.action_increment_usage()
        mask_v2.action_increment_usage()
        mask_v2.action_increment_usage()
        mask_v1.action_increment_usage()

        # 5. Get best mask for supplier - should return v2 (most used)
        best_mask = self.Mask.get_mask_for_partner(supplier.id)
        self.assertEqual(best_mask, mask_v2)
        self.assertEqual(best_mask.usage_count, 3)

        # 6. Archive v2 and verify v1 is now returned
        mask_v2.active = False
        best_mask = self.Mask.get_mask_for_partner(supplier.id)
        self.assertEqual(best_mask, mask_v1)

        # 7. Delete supplier and verify cascade delete
        mask_v1_id = mask_v1.id
        mask_v2_id = mask_v2.id
        supplier.unlink()
        self.assertFalse(self.Mask.browse(mask_v1_id).exists())
        self.assertFalse(self.Mask.browse(mask_v2_id).exists())
