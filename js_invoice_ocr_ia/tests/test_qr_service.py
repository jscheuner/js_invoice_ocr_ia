# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

"""Tests for Swiss QR-bill decoder service.

These tests verify SPC payload parsing and Swico billing information
extraction. QR image decoding itself is exercised only if a decoder
backend (zxing-cpp or pyzbar) is installed.
"""

import logging

from odoo.tests import TransactionCase, tagged

from odoo.addons.js_invoice_ocr_ia.services.qr_service import SwissQRService

_logger = logging.getLogger(__name__)


def build_spc_payload(**overrides):
    """Build a valid SPC v2.0 payload with optional field overrides."""
    fields = {
        'iban': 'CH4431999123000889012',
        'creditor_name': 'Robert Schneider AG',
        'amount': '1949.75',
        'currency': 'CHF',
        'ref_type': 'QRR',
        'reference': '210000000003139471430009017',
        'message': 'Commande du 15.06.2025',
        'billing_info': '//S1/10/10201409/11/250612/30/106017086/32/8.1/40/0:30',
    }
    fields.update(overrides)
    return '\n'.join([
        'SPC', '0200', '1', fields['iban'],
        'S', fields['creditor_name'], 'Rue du Lac', '1268', '2501', 'Biel', 'CH',
        '', '', '', '', '', '', '',
        fields['amount'], fields['currency'],
        'S', 'Pia Rutschmann', 'Marktgasse', '28', '9400', 'Rorschach', 'CH',
        fields['ref_type'], fields['reference'],
        fields['message'],
        'EPD',
        fields['billing_info'],
    ])


@tagged('post_install', '-at_install')
class TestSwissQRService(TransactionCase):
    """Test Swiss QR payload parsing."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service = SwissQRService()

    def test_parse_full_payload(self):
        """A complete SPC payload is parsed with all key fields."""
        result = self.service.parse_swiss_qr(build_spc_payload())

        self.assertEqual(result['iban'], 'CH4431999123000889012')
        self.assertEqual(result['creditor']['name'], 'Robert Schneider AG')
        self.assertEqual(result['amount'], 1949.75)
        self.assertEqual(result['currency'], 'CHF')
        self.assertEqual(result['reference_type'], 'QRR')
        self.assertEqual(result['reference'], '210000000003139471430009017')

    def test_parse_swico_billing_info(self):
        """Swico tags yield invoice number, normalized date and VAT number."""
        result = self.service.parse_swiss_qr(build_spc_payload())
        swico = result['swico']

        self.assertEqual(swico['invoice_number'], '10201409')
        self.assertEqual(swico['invoice_date'], '2025-06-12')
        self.assertEqual(swico['vat_number'], '106017086')

    def test_parse_non_spc_payload_returns_none(self):
        """Random QR content (URL, text) is not mistaken for a QR-bill."""
        self.assertIsNone(self.service.parse_swiss_qr('https://example.com'))
        self.assertIsNone(self.service.parse_swiss_qr(''))
        self.assertIsNone(self.service.parse_swiss_qr(None))

    def test_parse_reference_non_type(self):
        """Reference is blanked when the reference type is NON."""
        payload = build_spc_payload(ref_type='NON', reference='')
        result = self.service.parse_swiss_qr(payload)

        self.assertEqual(result['reference_type'], 'NON')
        self.assertEqual(result['reference'], '')

    def test_parse_no_amount(self):
        """QR-bills without amount (open amount) parse with amount None."""
        payload = build_spc_payload(amount='')
        result = self.service.parse_swiss_qr(payload)

        self.assertIsNone(result['amount'])

    def test_parse_no_billing_info(self):
        """Missing Swico info yields an empty swico dict."""
        payload = build_spc_payload(billing_info='')
        result = self.service.parse_swiss_qr(payload)

        self.assertEqual(result['swico'], {})

    def test_parse_swico_escaped_slash(self):
        """Escaped slashes in Swico values are unescaped."""
        swico = self.service.parse_swico('//S1/10/RE\\/2025\\/001/30/106017086')

        self.assertEqual(swico['invoice_number'], 'RE/2025/001')
        self.assertEqual(swico['vat_number'], '106017086')

    def test_crlf_line_endings(self):
        """Payloads with CRLF line endings are handled."""
        payload = build_spc_payload().replace('\n', '\r\n')
        result = self.service.parse_swiss_qr(payload)

        self.assertEqual(result['amount'], 1949.75)
