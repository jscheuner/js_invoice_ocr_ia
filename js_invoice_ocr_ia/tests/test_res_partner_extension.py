# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import json

from odoo.tests import TransactionCase


class TestResPartnerExtension(TransactionCase):
    """Tests for res.partner JSOCR extension.

    This test suite covers:
    - JSOCR fields exist on res.partner
    - add_alias() method
    - has_alias() method
    - get_aliases() method
    - remove_alias() method
    - find_by_alias() method
    - One2many relationship to jsocr.mask
    """

    def setUp(self):
        super().setUp()
        self.Partner = self.env['res.partner']
        self.Mask = self.env['jsocr.mask']
        self.Account = self.env['account.account']

        # Create test supplier
        self.test_partner = self.Partner.create({
            'name': 'Test JSOCR Supplier',
            'supplier_rank': 1,
        })

    # -------------------------------------------------------------------------
    # TEST: JSOCR fields exist
    # -------------------------------------------------------------------------

    def test_jsocr_aliases_field_exists(self):
        """Test: jsocr_aliases field exists on res.partner."""
        self.assertIn('jsocr_aliases', self.Partner._fields)

    def test_jsocr_default_account_id_field_exists(self):
        """Test: jsocr_default_account_id field exists on res.partner."""
        self.assertIn('jsocr_default_account_id', self.Partner._fields)

    def test_jsocr_mask_ids_field_exists(self):
        """Test: jsocr_mask_ids field exists on res.partner."""
        self.assertIn('jsocr_mask_ids', self.Partner._fields)

    def test_jsocr_aliases_default_empty(self):
        """Test: jsocr_aliases is empty/False by default."""
        partner = self.Partner.create({'name': 'New Partner'})
        self.assertFalse(partner.jsocr_aliases)

    def test_jsocr_default_account_id_default_empty(self):
        """Test: jsocr_default_account_id is empty by default."""
        partner = self.Partner.create({'name': 'New Partner'})
        self.assertFalse(partner.jsocr_default_account_id)

    # -------------------------------------------------------------------------
    # TEST: add_alias() method
    # -------------------------------------------------------------------------

    def test_add_alias_first_alias(self):
        """Test: add_alias adds first alias correctly."""
        result = self.test_partner.add_alias('Alias One')

        self.assertTrue(result)
        aliases = json.loads(self.test_partner.jsocr_aliases)
        self.assertEqual(aliases, ['Alias One'])

    def test_add_alias_multiple(self):
        """Test: add_alias adds multiple aliases correctly."""
        self.test_partner.add_alias('Alias One')
        self.test_partner.add_alias('Alias Two')
        self.test_partner.add_alias('Alias Three')

        aliases = json.loads(self.test_partner.jsocr_aliases)
        self.assertEqual(len(aliases), 3)
        self.assertIn('Alias One', aliases)
        self.assertIn('Alias Two', aliases)
        self.assertIn('Alias Three', aliases)

    def test_add_alias_duplicate_returns_false(self):
        """Test: add_alias returns False for duplicate alias."""
        self.test_partner.add_alias('Duplicate')
        result = self.test_partner.add_alias('Duplicate')

        self.assertFalse(result)
        aliases = json.loads(self.test_partner.jsocr_aliases)
        self.assertEqual(aliases.count('Duplicate'), 1)

    def test_add_alias_empty_string_returns_false(self):
        """Test: add_alias returns False for empty string."""
        result = self.test_partner.add_alias('')

        self.assertFalse(result)

    def test_add_alias_none_returns_false(self):
        """Test: add_alias returns False for None."""
        result = self.test_partner.add_alias(None)

        self.assertFalse(result)

    def test_add_alias_whitespace_only_returns_false(self):
        """Test: add_alias returns False for whitespace-only string."""
        result = self.test_partner.add_alias('   ')

        self.assertFalse(result)

    def test_add_alias_strips_whitespace(self):
        """Test: add_alias strips leading/trailing whitespace."""
        self.test_partner.add_alias('  Trimmed Alias  ')

        aliases = json.loads(self.test_partner.jsocr_aliases)
        self.assertIn('Trimmed Alias', aliases)

    def test_add_alias_with_corrupted_json(self):
        """Test: add_alias handles corrupted jsocr_aliases gracefully."""
        self.test_partner.jsocr_aliases = 'not valid json'

        result = self.test_partner.add_alias('New Alias')

        self.assertTrue(result)
        aliases = json.loads(self.test_partner.jsocr_aliases)
        self.assertEqual(aliases, ['New Alias'])

    # -------------------------------------------------------------------------
    # TEST: has_alias() method
    # -------------------------------------------------------------------------

    def test_has_alias_exists(self):
        """Test: has_alias returns True when alias exists."""
        self.test_partner.add_alias('Existing Alias')

        result = self.test_partner.has_alias('Existing Alias')

        self.assertTrue(result)

    def test_has_alias_not_exists(self):
        """Test: has_alias returns False when alias doesn't exist."""
        self.test_partner.add_alias('Other Alias')

        result = self.test_partner.has_alias('Non Existing')

        self.assertFalse(result)

    def test_has_alias_empty_list(self):
        """Test: has_alias returns False for empty alias list."""
        result = self.test_partner.has_alias('Any Alias')

        self.assertFalse(result)

    def test_has_alias_none_returns_false(self):
        """Test: has_alias returns False for None input."""
        self.test_partner.add_alias('Some Alias')

        result = self.test_partner.has_alias(None)

        self.assertFalse(result)

    def test_has_alias_empty_string_returns_false(self):
        """Test: has_alias returns False for empty string."""
        self.test_partner.add_alias('Some Alias')

        result = self.test_partner.has_alias('')

        self.assertFalse(result)

    def test_has_alias_with_corrupted_json(self):
        """Test: has_alias handles corrupted jsocr_aliases gracefully."""
        self.test_partner.jsocr_aliases = 'not valid json'

        result = self.test_partner.has_alias('Any Alias')

        self.assertFalse(result)

    # -------------------------------------------------------------------------
    # TEST: get_aliases() method
    # -------------------------------------------------------------------------

    def test_get_aliases_returns_list(self):
        """Test: get_aliases returns list of aliases."""
        self.test_partner.add_alias('Alias A')
        self.test_partner.add_alias('Alias B')

        aliases = self.test_partner.get_aliases()

        self.assertIsInstance(aliases, list)
        self.assertEqual(len(aliases), 2)

    def test_get_aliases_empty_returns_empty_list(self):
        """Test: get_aliases returns empty list when no aliases."""
        aliases = self.test_partner.get_aliases()

        self.assertEqual(aliases, [])

    def test_get_aliases_with_corrupted_json(self):
        """Test: get_aliases handles corrupted JSON gracefully."""
        self.test_partner.jsocr_aliases = 'invalid'

        aliases = self.test_partner.get_aliases()

        self.assertEqual(aliases, [])

    # -------------------------------------------------------------------------
    # TEST: remove_alias() method
    # -------------------------------------------------------------------------

    def test_remove_alias_exists(self):
        """Test: remove_alias removes existing alias."""
        self.test_partner.add_alias('To Remove')
        self.test_partner.add_alias('To Keep')

        result = self.test_partner.remove_alias('To Remove')

        self.assertTrue(result)
        self.assertFalse(self.test_partner.has_alias('To Remove'))
        self.assertTrue(self.test_partner.has_alias('To Keep'))

    def test_remove_alias_not_exists(self):
        """Test: remove_alias returns False when alias not found."""
        self.test_partner.add_alias('Existing')

        result = self.test_partner.remove_alias('Non Existing')

        self.assertFalse(result)

    def test_remove_alias_empty_returns_false(self):
        """Test: remove_alias returns False for empty input."""
        result = self.test_partner.remove_alias('')

        self.assertFalse(result)

    # -------------------------------------------------------------------------
    # TEST: find_by_alias() method
    # -------------------------------------------------------------------------

    def test_find_by_alias_found(self):
        """Test: find_by_alias finds partner with matching alias."""
        self.test_partner.add_alias('Findable Alias')

        found = self.Partner.find_by_alias('Findable Alias')

        self.assertEqual(found, self.test_partner)

    def test_find_by_alias_not_found(self):
        """Test: find_by_alias returns False when no match."""
        self.test_partner.add_alias('Other Alias')

        found = self.Partner.find_by_alias('Non Existing')

        self.assertIs(found, False)

    def test_find_by_alias_empty_returns_false(self):
        """Test: find_by_alias returns False for empty input."""
        found = self.Partner.find_by_alias('')

        self.assertIs(found, False)

    def test_find_by_alias_none_returns_false(self):
        """Test: find_by_alias returns False for None input."""
        found = self.Partner.find_by_alias(None)

        self.assertIs(found, False)

    # -------------------------------------------------------------------------
    # TEST: One2many jsocr_mask_ids
    # -------------------------------------------------------------------------

    def test_jsocr_mask_ids_empty_by_default(self):
        """Test: jsocr_mask_ids is empty for new partner."""
        self.assertEqual(len(self.test_partner.jsocr_mask_ids), 0)

    def test_jsocr_mask_ids_shows_related_masks(self):
        """Test: jsocr_mask_ids shows masks linked to partner."""
        mask1 = self.Mask.create({
            'name': 'Mask 1',
            'partner_id': self.test_partner.id,
        })
        mask2 = self.Mask.create({
            'name': 'Mask 2',
            'partner_id': self.test_partner.id,
        })

        self.assertEqual(len(self.test_partner.jsocr_mask_ids), 2)
        self.assertIn(mask1, self.test_partner.jsocr_mask_ids)
        self.assertIn(mask2, self.test_partner.jsocr_mask_ids)

    def test_jsocr_mask_ids_excludes_other_partner_masks(self):
        """Test: jsocr_mask_ids only shows masks for this partner."""
        other_partner = self.Partner.create({'name': 'Other Partner'})
        self.Mask.create({
            'name': 'Our Mask',
            'partner_id': self.test_partner.id,
        })
        other_mask = self.Mask.create({
            'name': 'Other Mask',
            'partner_id': other_partner.id,
        })

        self.assertEqual(len(self.test_partner.jsocr_mask_ids), 1)
        self.assertNotIn(other_mask, self.test_partner.jsocr_mask_ids)

    # -------------------------------------------------------------------------
    # TEST: jsocr_default_account_id
    # -------------------------------------------------------------------------

    def test_set_default_account(self):
        """Test: jsocr_default_account_id can be set."""
        # Find any expense account to use for testing
        account = self.Account.search([('account_type', '=', 'expense')], limit=1)
        if not account:
            # Create a basic test account if none exists
            account = self.Account.create({
                'name': 'Test Expense Account',
                'code': 'JSOCR001',
                'account_type': 'expense',
            })

        self.test_partner.jsocr_default_account_id = account.id

        self.assertEqual(self.test_partner.jsocr_default_account_id, account)

    # -------------------------------------------------------------------------
    # TEST: Integration
    # -------------------------------------------------------------------------

    def test_full_alias_workflow(self):
        """Test: complete alias workflow."""
        partner = self.Partner.create({
            'name': 'Workflow Test Partner',
            'supplier_rank': 1,
        })

        # Add aliases
        partner.add_alias('Primary Name')
        partner.add_alias('Secondary Name')
        partner.add_alias('Third Name')

        # Verify count
        self.assertEqual(len(partner.get_aliases()), 3)

        # Find by alias
        found = self.Partner.find_by_alias('Secondary Name')
        self.assertEqual(found, partner)

        # Remove one
        partner.remove_alias('Secondary Name')
        self.assertFalse(partner.has_alias('Secondary Name'))
        self.assertEqual(len(partner.get_aliases()), 2)

        # Cannot find removed alias
        not_found = self.Partner.find_by_alias('Secondary Name')
        self.assertIs(not_found, False)
