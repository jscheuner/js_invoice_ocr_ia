# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import base64
import json
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'jsocr')
class TestHtTtcDetection(TransactionCase):
    """Tests for HT/TTC detection and price adjustment in invoice creation.

    This test suite covers the tech-spec "Controle intelligent HT/TTC et validation total facture":
    - _detect_amounts_type: Detection of whether extracted amounts are HT or TTC
    - _get_tax_for_account: Retrieving tax info for an account
    - _adjust_price_unit: Converting prices based on tax expectations
    - _validate_invoice_total: Post-creation total validation
    - Integration with _create_invoice_lines
    """

    def setUp(self):
        super().setUp()
        self.Job = self.env['jsocr.import.job']
        self.Account = self.env['account.account']
        self.Tax = self.env['account.tax']
        self.Partner = self.env['res.partner']

        # Fake PDF content
        self.fake_pdf = base64.b64encode(b'%PDF-1.4 fake content')

        # Create test supplier
        self.supplier = self.Partner.create({
            'name': 'Test Supplier HT/TTC',
            'supplier_rank': 1,
        })

        # Create expense account for tests
        self.expense_account = self.Account.search([
            ('code', '=like', '6%'),
            ('account_type', 'in', ('expense', 'expense_depreciation', 'expense_direct_cost')),
        ], limit=1)

        if not self.expense_account:
            # Create one if not found
            self.expense_account = self.Account.create({
                'code': '6000',
                'name': 'Test Expense Account',
                'account_type': 'expense',
            })

        # Create tax HT (tax excluded) - TVA 8.1%
        self.tax_ht = self.Tax.create({
            'name': 'TVA 8.1% HT',
            'amount': 8.1,
            'type_tax_use': 'purchase',
            'price_include_override': 'tax_excluded',
        })

        # Create tax TTC (tax included) - TVA 8.1%
        self.tax_ttc = self.Tax.create({
            'name': 'TVA 8.1% TTC',
            'amount': 8.1,
            'type_tax_use': 'purchase',
            'price_include_override': 'tax_included',
        })

        # Create tax with fallback on price_include
        self.tax_fallback_ttc = self.Tax.create({
            'name': 'TVA 8.1% Fallback TTC',
            'amount': 8.1,
            'type_tax_use': 'purchase',
            'price_include_override': False,
            'price_include': True,
        })

        # Create account with HT tax
        self.account_ht = self.Account.create({
            'code': '6100',
            'name': 'Test Account HT',
            'account_type': 'expense',
            'tax_ids': [(6, 0, [self.tax_ht.id])],
        })

        # Create account with TTC tax
        self.account_ttc = self.Account.create({
            'code': '6200',
            'name': 'Test Account TTC',
            'account_type': 'expense',
            'tax_ids': [(6, 0, [self.tax_ttc.id])],
        })

        # Create account with no tax
        self.account_no_tax = self.Account.create({
            'code': '6300',
            'name': 'Test Account No Tax',
            'account_type': 'expense',
        })

        # Create account with multi-taxes (8.1% + 2%)
        self.tax_eco = self.Tax.create({
            'name': 'Eco-taxe 2%',
            'amount': 2.0,
            'type_tax_use': 'purchase',
            'price_include_override': 'tax_excluded',
        })
        self.account_multi_tax = self.Account.create({
            'code': '6400',
            'name': 'Test Account Multi Tax',
            'account_type': 'expense',
            'tax_ids': [(6, 0, [self.tax_ht.id, self.tax_eco.id])],
        })

        # Create account with fallback TTC tax
        self.account_fallback_ttc = self.Account.create({
            'code': '6500',
            'name': 'Test Account Fallback TTC',
            'account_type': 'expense',
            'tax_ids': [(6, 0, [self.tax_fallback_ttc.id])],
        })

    def _create_job(self, **kwargs):
        """Create a job with default values for testing."""
        vals = {
            'pdf_filename': 'test_ht_ttc.pdf',
            'pdf_file': self.fake_pdf,
        }
        vals.update(kwargs)
        return self.Job.create(vals)

    # -------------------------------------------------------------------------
    # TEST: _detect_amounts_type
    # -------------------------------------------------------------------------

    def test_detect_amounts_type_ht(self):
        """Test: lines sum matches extracted_amount_untaxed -> returns 'ht'"""
        job = self._create_job(
            extracted_amount_untaxed=100.0,
            extracted_amount_total=108.10,
        )
        lines = [
            {'unit_price': 50.0, 'quantity': 1.0},
            {'unit_price': 50.0, 'quantity': 1.0},
        ]

        result = job._detect_amounts_type(lines)

        self.assertEqual(result, 'ht')

    def test_detect_amounts_type_ttc(self):
        """Test: lines sum matches extracted_amount_total -> returns 'ttc'"""
        job = self._create_job(
            extracted_amount_untaxed=92.51,
            extracted_amount_total=100.0,
        )
        lines = [
            {'unit_price': 50.0, 'quantity': 1.0},
            {'unit_price': 50.0, 'quantity': 1.0},
        ]

        result = job._detect_amounts_type(lines)

        self.assertEqual(result, 'ttc')

    def test_detect_amounts_type_unknown(self):
        """Test: lines sum matches neither total -> returns 'unknown'"""
        job = self._create_job(
            extracted_amount_untaxed=200.0,
            extracted_amount_total=216.20,
        )
        lines = [
            {'unit_price': 50.0, 'quantity': 1.0},
        ]  # Sum = 50, doesn't match either

        result = job._detect_amounts_type(lines)

        self.assertEqual(result, 'unknown')

    def test_detect_amounts_type_no_tax(self):
        """Test: when HT = TTC (no tax), returns 'ht' (tested first per spec)"""
        job = self._create_job(
            extracted_amount_untaxed=100.0,
            extracted_amount_total=100.0,
        )
        lines = [
            {'unit_price': 100.0, 'quantity': 1.0},
        ]

        result = job._detect_amounts_type(lines)

        # HT is tested first, so should return 'ht'
        self.assertEqual(result, 'ht')

    def test_detect_amounts_type_empty_lines(self):
        """Test: empty lines list -> returns 'unknown'"""
        job = self._create_job(
            extracted_amount_untaxed=100.0,
            extracted_amount_total=108.10,
        )

        result = job._detect_amounts_type([])

        self.assertEqual(result, 'unknown')

    def test_detect_amounts_type_null_totals(self):
        """Test: extracted_amount_* = None or 0 -> returns 'unknown'"""
        job = self._create_job(
            extracted_amount_untaxed=0.0,
            extracted_amount_total=0.0,
        )
        lines = [{'unit_price': 100.0, 'quantity': 1.0}]

        result = job._detect_amounts_type(lines)

        self.assertEqual(result, 'unknown')

    def test_detect_amounts_type_negative_quantities(self):
        """Test: credit note with negative quantities -> detection works with abs()"""
        job = self._create_job(
            extracted_amount_untaxed=100.0,
            extracted_amount_total=108.10,
        )
        # Credit note: negative quantities
        lines = [
            {'unit_price': 50.0, 'quantity': -1.0},
            {'unit_price': 50.0, 'quantity': -1.0},
        ]

        result = job._detect_amounts_type(lines)

        # abs(50 * -1) + abs(50 * -1) = 100, matches extracted_amount_untaxed
        self.assertEqual(result, 'ht')

    # -------------------------------------------------------------------------
    # TEST: _get_tax_for_account
    # -------------------------------------------------------------------------

    def test_get_tax_for_account_with_purchase_tax(self):
        """Test: account with purchase tax -> returns tax info"""
        job = self._create_job()

        result = job._get_tax_for_account(self.account_ht.id)

        self.assertIsNotNone(result)
        self.assertEqual(result['tax_rate'], 8.1)
        self.assertFalse(result['tax_expects_ttc'])

    def test_get_tax_for_account_no_tax(self):
        """Test: account without tax -> returns None"""
        job = self._create_job()

        result = job._get_tax_for_account(self.account_no_tax.id)

        self.assertIsNone(result)

    def test_get_tax_for_account_multi_taxes(self):
        """Test: account with 2 taxes -> combined rate"""
        job = self._create_job()

        result = job._get_tax_for_account(self.account_multi_tax.id)

        self.assertIsNotNone(result)
        # 8.1% + 2% = 10.1%
        self.assertAlmostEqual(result['tax_rate'], 10.1, places=1)
        self.assertFalse(result['tax_expects_ttc'])

    def test_get_tax_for_account_invalid_account(self):
        """Test: account_id = None -> returns None"""
        job = self._create_job()

        result = job._get_tax_for_account(None)

        self.assertIsNone(result)

    def test_get_tax_for_account_ttc_tax(self):
        """Test: account with TTC tax -> tax_expects_ttc = True"""
        job = self._create_job()

        result = job._get_tax_for_account(self.account_ttc.id)

        self.assertIsNotNone(result)
        self.assertTrue(result['tax_expects_ttc'])

    # -------------------------------------------------------------------------
    # TEST: _adjust_price_unit
    # -------------------------------------------------------------------------

    def test_adjust_price_ht_to_ttc(self):
        """Test: HT amounts + tax expects TTC -> price converted to TTC"""
        job = self._create_job()
        tax_info = {'tax_rate': 8.1, 'tax_expects_ttc': True}

        adjusted, was_adjusted = job._adjust_price_unit(100.0, 'ht', tax_info)

        self.assertTrue(was_adjusted)
        self.assertAlmostEqual(adjusted, 108.10, places=2)

    def test_adjust_price_ttc_to_ht(self):
        """Test: TTC amounts + tax expects HT -> price converted to HT"""
        job = self._create_job()
        tax_info = {'tax_rate': 8.1, 'tax_expects_ttc': False}

        adjusted, was_adjusted = job._adjust_price_unit(108.10, 'ttc', tax_info)

        self.assertTrue(was_adjusted)
        self.assertAlmostEqual(adjusted, 100.0, places=2)

    def test_adjust_price_no_conversion_ht_to_ht(self):
        """Test: HT amounts + tax expects HT -> no conversion"""
        job = self._create_job()
        tax_info = {'tax_rate': 8.1, 'tax_expects_ttc': False}

        adjusted, was_adjusted = job._adjust_price_unit(100.0, 'ht', tax_info)

        self.assertFalse(was_adjusted)
        self.assertEqual(adjusted, 100.0)

    def test_adjust_price_no_conversion_ttc_to_ttc(self):
        """Test: TTC amounts + tax expects TTC -> no conversion"""
        job = self._create_job()
        tax_info = {'tax_rate': 8.1, 'tax_expects_ttc': True}

        adjusted, was_adjusted = job._adjust_price_unit(108.10, 'ttc', tax_info)

        self.assertFalse(was_adjusted)
        self.assertEqual(adjusted, 108.10)

    def test_adjust_price_unknown(self):
        """Test: unknown amounts type -> no conversion"""
        job = self._create_job()
        tax_info = {'tax_rate': 8.1, 'tax_expects_ttc': True}

        adjusted, was_adjusted = job._adjust_price_unit(100.0, 'unknown', tax_info)

        self.assertFalse(was_adjusted)
        self.assertEqual(adjusted, 100.0)

    def test_adjust_price_division_by_zero(self):
        """Test: invalid tax_rate = -100 -> no crash, price unchanged"""
        job = self._create_job()
        tax_info = {'tax_rate': -100.0, 'tax_expects_ttc': False}

        adjusted, was_adjusted = job._adjust_price_unit(100.0, 'ttc', tax_info)

        self.assertFalse(was_adjusted)
        self.assertEqual(adjusted, 100.0)

    def test_adjust_price_rounding(self):
        """Test: price is rounded to 2 decimals"""
        job = self._create_job()
        tax_info = {'tax_rate': 7.7, 'tax_expects_ttc': True}  # Swiss TVA

        adjusted, was_adjusted = job._adjust_price_unit(100.0, 'ht', tax_info)

        self.assertTrue(was_adjusted)
        # 100 * 1.077 = 107.7
        self.assertEqual(adjusted, 107.70)
        # Verify it's exactly 2 decimals
        self.assertEqual(len(str(adjusted).split('.')[1]) if '.' in str(adjusted) else 0, 1)

    def test_adjust_price_no_tax_info(self):
        """Test: tax_info = None -> no conversion"""
        job = self._create_job()

        adjusted, was_adjusted = job._adjust_price_unit(100.0, 'ht', None)

        self.assertFalse(was_adjusted)
        self.assertEqual(adjusted, 100.0)

    # -------------------------------------------------------------------------
    # TEST: _validate_invoice_total
    # -------------------------------------------------------------------------

    def test_validate_total_ok(self):
        """Test: ecart <= 0.03 -> mismatch = False, returns True"""
        job = self._create_job(
            extracted_amount_total=100.0,
            partner_id=self.supplier.id,
        )

        # Create invoice with matching total
        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.supplier.id,
        })
        # Manually set amount_total for test (normally computed)
        invoice._compute_amount()

        # Simulate total matching (within tolerance)
        job.extracted_amount_total = invoice.amount_total + 0.02

        result = job._validate_invoice_total(invoice)

        self.assertTrue(result)
        self.assertFalse(invoice.jsocr_amount_mismatch)

    def test_validate_total_mismatch(self):
        """Test: ecart > 0.03 -> mismatch = True, confidence reduced"""
        job = self._create_job(
            extracted_amount_total=100.0,
            partner_id=self.supplier.id,
        )

        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.supplier.id,
        })

        # Large mismatch
        job.extracted_amount_total = 150.0

        result = job._validate_invoice_total(invoice)

        self.assertFalse(result)
        self.assertTrue(invoice.jsocr_amount_mismatch)

    def test_validate_total_null_extracted(self):
        """Test: extracted_amount_total = None -> validation skipped, returns True"""
        job = self._create_job(
            extracted_amount_total=0.0,
        )

        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.supplier.id,
        })

        result = job._validate_invoice_total(invoice)

        self.assertTrue(result)

    # -------------------------------------------------------------------------
    # TEST: price_include fallback
    # -------------------------------------------------------------------------

    def test_price_include_fallback(self):
        """Test: price_include_override = False, price_include = True -> TTC"""
        job = self._create_job()

        result = job._get_tax_for_account(self.account_fallback_ttc.id)

        self.assertIsNotNone(result)
        self.assertTrue(result['tax_expects_ttc'])

    # -------------------------------------------------------------------------
    # TEST: Integration - _create_invoice_lines with adjustment
    # -------------------------------------------------------------------------

    def test_create_invoice_lines_with_ht_to_ttc_adjustment(self):
        """Test: full integration - HT amounts converted to TTC for TTC tax account"""
        # Set supplier's default account to TTC account
        self.supplier.jsocr_default_account_id = self.account_ttc.id

        job = self._create_job(
            partner_id=self.supplier.id,
            extracted_amount_untaxed=100.0,
            extracted_amount_total=108.10,
            extracted_lines=json.dumps([
                {'description': 'Test line', 'unit_price': 100.0, 'quantity': 1.0},
            ]),
        )

        # Create invoice
        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.supplier.id,
            'jsocr_import_job_id': job.id,
        })

        # Create lines
        job._create_invoice_lines(invoice)

        # Check that price was adjusted
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        line = invoice.invoice_line_ids[0]
        # HT 100.0 -> TTC 108.10
        self.assertAlmostEqual(line.price_unit, 108.10, places=2)

    def test_create_invoice_lines_unknown_type_sets_mismatch(self):
        """Test: unknown amounts type sets jsocr_amount_mismatch = True"""
        self.supplier.jsocr_default_account_id = self.account_ht.id

        job = self._create_job(
            partner_id=self.supplier.id,
            extracted_amount_untaxed=200.0,
            extracted_amount_total=216.20,
            extracted_lines=json.dumps([
                {'description': 'Test line', 'unit_price': 50.0, 'quantity': 1.0},
            ]),  # Sum = 50, doesn't match either total
        )

        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.supplier.id,
            'jsocr_import_job_id': job.id,
        })

        job._create_invoice_lines(invoice)

        self.assertTrue(invoice.jsocr_amount_mismatch)
        # Price should remain unchanged
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 50.0)


@tagged('post_install', '-at_install', 'jsocr')
class TestAmountMismatchField(TransactionCase):
    """Tests for jsocr_amount_mismatch field on account.move."""

    def setUp(self):
        super().setUp()
        self.Partner = self.env['res.partner']
        self.supplier = self.Partner.create({
            'name': 'Test Supplier Mismatch',
            'supplier_rank': 1,
        })

    def test_jsocr_amount_mismatch_default_false(self):
        """Test: jsocr_amount_mismatch defaults to False"""
        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.supplier.id,
        })

        self.assertFalse(invoice.jsocr_amount_mismatch)

    def test_jsocr_amount_mismatch_can_be_set_true(self):
        """Test: jsocr_amount_mismatch can be set to True"""
        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.supplier.id,
        })

        invoice.jsocr_amount_mismatch = True

        self.assertTrue(invoice.jsocr_amount_mismatch)
