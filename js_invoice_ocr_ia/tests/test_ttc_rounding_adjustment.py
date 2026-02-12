# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import base64
import json
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install', 'jsocr', 'jsocr_ttc_rounding')
class TestTtcRoundingAdjustment(TransactionCase):
    """Tests for automatic TTC rounding adjustment on tax lines.

    Covers the feature that adjusts the tax line balance so that the
    invoice TTC matches the extracted TTC when the difference is within
    the configured threshold.
    """

    def setUp(self):
        super().setUp()
        self.Job = self.env['jsocr.import.job']
        self.Config = self.env['jsocr.config']
        self.Account = self.env['account.account']
        self.Tax = self.env['account.tax']
        self.Partner = self.env['res.partner']

        # Fake PDF
        self.fake_pdf = base64.b64encode(b'%PDF-1.4 fake content')

        # Config singleton
        self.config = self.Config.get_config()

        # Create test supplier
        self.supplier = self.Partner.create({
            'name': 'Supplier TTC Rounding',
            'supplier_rank': 1,
        })

        # Create expense account with HT tax (8.1%)
        self.tax_ht = self.Tax.create({
            'name': 'TVA 8.1% HT Test',
            'amount': 8.1,
            'type_tax_use': 'purchase',
            'price_include_override': 'tax_excluded',
        })

        self.expense_account = self.Account.search([
            ('code', '=like', '6%'),
            ('account_type', 'in', ('expense', 'expense_depreciation', 'expense_direct_cost')),
        ], limit=1)

        if not self.expense_account:
            self.expense_account = self.Account.create({
                'code': '6000',
                'name': 'Test Expense Account',
                'account_type': 'expense',
            })

        # Set default account on supplier so lines get created
        self.supplier.jsocr_default_account_id = self.expense_account.id

        # Assign tax to account
        self.expense_account.write({'tax_ids': [(6, 0, [self.tax_ht.id])]})

    def _create_job_with_amounts(self, line_price, extracted_total, extracted_untaxed=0.0, extracted_tax=0.0):
        """Helper to create a job with specific amounts and run invoice creation."""
        lines = [{'description': 'Test line', 'quantity': 1.0, 'unit_price': line_price}]
        job = self.Job.create({
            'pdf_file': self.fake_pdf,
            'pdf_filename': 'test_rounding.pdf',
            'state': 'processing',
            'partner_id': self.supplier.id,
            'extracted_supplier_name': self.supplier.name,
            'extracted_lines': json.dumps(lines),
            'extracted_amount_untaxed': extracted_untaxed or line_price,
            'extracted_amount_tax': extracted_tax,
            'extracted_amount_total': extracted_total,
        })
        return job

    # -----------------------------------------------------------------
    # Test 1: Option disabled by default -> no adjustment
    # -----------------------------------------------------------------
    def test_01_option_disabled_no_adjustment(self):
        """When adjust_ttc_rounding is False, no adjustment is applied."""
        self.config.adjust_ttc_rounding = False

        # Create a job where Odoo total will differ from extracted by 0.02
        # line_price = 100, tax 8.1% -> Odoo computes 108.10
        # We set extracted_total = 108.12 (diff = 0.02)
        job = self._create_job_with_amounts(
            line_price=100.0,
            extracted_total=108.12,
            extracted_untaxed=100.0,
            extracted_tax=8.12,
        )
        invoice = job._create_draft_invoice()

        self.assertEqual(invoice.jsocr_ttc_adjustment, 0.0)

    # -----------------------------------------------------------------
    # Test 2: Diff of 0.02 with option enabled -> adjustment applied
    # -----------------------------------------------------------------
    def test_02_adjustment_applied(self):
        """A small diff (0.02) is corrected when option is enabled."""
        self.config.write({
            'adjust_ttc_rounding': True,
            'adjust_ttc_max_diff': 0.05,
        })

        job = self._create_job_with_amounts(
            line_price=100.0,
            extracted_total=108.12,
            extracted_untaxed=100.0,
            extracted_tax=8.12,
        )
        invoice = job._create_draft_invoice()

        # Check the adjustment was recorded
        self.assertNotEqual(invoice.jsocr_ttc_adjustment, 0.0)
        # The invoice total should now match the extracted total
        self.assertAlmostEqual(invoice.amount_total, 108.12, places=2)
        # Mismatch flag should be cleared by _validate_invoice_total
        self.assertFalse(invoice.jsocr_amount_mismatch)

    # -----------------------------------------------------------------
    # Test 3: Diff exceeds threshold -> no adjustment
    # -----------------------------------------------------------------
    def test_03_diff_exceeds_threshold(self):
        """A diff larger than max_diff is NOT adjusted."""
        self.config.write({
            'adjust_ttc_rounding': True,
            'adjust_ttc_max_diff': 0.05,
        })

        # line 100 -> Odoo 108.10, extracted 108.20 -> diff = 0.10 > 0.05
        job = self._create_job_with_amounts(
            line_price=100.0,
            extracted_total=108.20,
            extracted_untaxed=100.0,
            extracted_tax=8.20,
        )
        invoice = job._create_draft_invoice()

        self.assertEqual(invoice.jsocr_ttc_adjustment, 0.0)

    # -----------------------------------------------------------------
    # Test 4: Diff == 0 -> no adjustment
    # -----------------------------------------------------------------
    def test_04_no_diff_no_adjustment(self):
        """When computed and extracted totals match exactly, no adjustment."""
        self.config.write({
            'adjust_ttc_rounding': True,
            'adjust_ttc_max_diff': 0.05,
        })

        # line 100 -> Odoo 108.10, extracted 108.10
        job = self._create_job_with_amounts(
            line_price=100.0,
            extracted_total=108.10,
            extracted_untaxed=100.0,
            extracted_tax=8.10,
        )
        invoice = job._create_draft_invoice()

        self.assertEqual(invoice.jsocr_ttc_adjustment, 0.0)

    # -----------------------------------------------------------------
    # Test 5: No tax line -> no adjustment
    # -----------------------------------------------------------------
    def test_05_no_tax_line_no_adjustment(self):
        """When there is no tax line, adjustment is skipped gracefully."""
        self.config.write({
            'adjust_ttc_rounding': True,
            'adjust_ttc_max_diff': 0.05,
        })

        # Remove taxes from account so no tax line is generated
        self.expense_account.write({'tax_ids': [(5, 0, 0)]})

        job = self._create_job_with_amounts(
            line_price=100.0,
            extracted_total=100.02,
            extracted_untaxed=100.0,
        )
        invoice = job._create_draft_invoice()

        self.assertEqual(invoice.jsocr_ttc_adjustment, 0.0)

    # -----------------------------------------------------------------
    # Test 6: Multiple tax lines -> adjustment on the largest
    # -----------------------------------------------------------------
    def test_06_multiple_tax_lines_largest_adjusted(self):
        """When multiple tax lines exist, the largest by abs(balance) is adjusted."""
        self.config.write({
            'adjust_ttc_rounding': True,
            'adjust_ttc_max_diff': 0.05,
        })

        # Add a second smaller tax
        tax_small = self.Tax.create({
            'name': 'TVA 2.6% HT Test',
            'amount': 2.6,
            'type_tax_use': 'purchase',
            'price_include_override': 'tax_excluded',
        })
        self.expense_account.write({'tax_ids': [(6, 0, [self.tax_ht.id, tax_small.id])]})

        # line 100 -> Odoo: 100 + 8.10 + 2.60 = 110.70
        # extracted 110.72 -> diff = 0.02
        job = self._create_job_with_amounts(
            line_price=100.0,
            extracted_total=110.72,
            extracted_untaxed=100.0,
            extracted_tax=10.72,
        )
        invoice = job._create_draft_invoice()

        self.assertNotEqual(invoice.jsocr_ttc_adjustment, 0.0)
        self.assertAlmostEqual(invoice.amount_total, 110.72, places=2)

    # -----------------------------------------------------------------
    # Test 7: Balance preserved after adjustment (sum of balances == 0)
    # -----------------------------------------------------------------
    def test_07_balance_preserved(self):
        """After adjustment, the sum of all line balances must remain zero."""
        self.config.write({
            'adjust_ttc_rounding': True,
            'adjust_ttc_max_diff': 0.05,
        })

        job = self._create_job_with_amounts(
            line_price=100.0,
            extracted_total=108.12,
            extracted_untaxed=100.0,
            extracted_tax=8.12,
        )
        invoice = job._create_draft_invoice()

        total_balance = sum(invoice.line_ids.mapped('balance'))
        self.assertAlmostEqual(total_balance, 0.0, places=2)

    # -----------------------------------------------------------------
    # Test 8: jsocr_ttc_adjustment field correctly filled
    # -----------------------------------------------------------------
    def test_08_adjustment_field_value(self):
        """The jsocr_ttc_adjustment field stores the exact diff applied."""
        self.config.write({
            'adjust_ttc_rounding': True,
            'adjust_ttc_max_diff': 0.05,
        })

        job = self._create_job_with_amounts(
            line_price=100.0,
            extracted_total=108.12,
            extracted_untaxed=100.0,
            extracted_tax=8.12,
        )
        invoice = job._create_draft_invoice()

        # diff = 108.12 - 108.10 = 0.02
        self.assertAlmostEqual(invoice.jsocr_ttc_adjustment, 0.02, places=2)

    # -----------------------------------------------------------------
    # Test 9: Config constraint - negative max_diff -> ValidationError
    # -----------------------------------------------------------------
    def test_09_config_constraint_negative_max_diff(self):
        """Setting adjust_ttc_max_diff to a negative value raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.config.write({'adjust_ttc_max_diff': -0.01})

    # -----------------------------------------------------------------
    # Test 10: Config constraint - max_diff > 1.0 -> ValidationError
    # -----------------------------------------------------------------
    def test_10_config_constraint_max_diff_too_large(self):
        """Setting adjust_ttc_max_diff above 1.0 raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.config.write({'adjust_ttc_max_diff': 1.5})

    # -----------------------------------------------------------------
    # Test 11: Negative diff (Odoo > extracted) -> adjustment decreases
    # -----------------------------------------------------------------
    def test_11_negative_diff_adjustment(self):
        """When Odoo total > extracted, the adjustment is negative."""
        self.config.write({
            'adjust_ttc_rounding': True,
            'adjust_ttc_max_diff': 0.05,
        })

        # line 100 -> Odoo 108.10, extracted 108.08 -> diff = -0.02
        job = self._create_job_with_amounts(
            line_price=100.0,
            extracted_total=108.08,
            extracted_untaxed=100.0,
            extracted_tax=8.08,
        )
        invoice = job._create_draft_invoice()

        self.assertAlmostEqual(invoice.jsocr_ttc_adjustment, -0.02, places=2)
        self.assertAlmostEqual(invoice.amount_total, 108.08, places=2)
