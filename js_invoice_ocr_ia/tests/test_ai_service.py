# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

"""Tests for OllamaService (AI invoice extraction).

These tests cover Stories 4.1-4.7:
- Story 4.1: Ollama connection and request
- Story 4.2: Structured extraction prompt
- Story 4.3: Supplier extraction
- Story 4.4: Date and invoice number extraction
- Story 4.5: Invoice lines extraction
- Story 4.6: Amounts extraction
- Story 4.7: Confidence calculation
"""

import json
from unittest.mock import patch, MagicMock

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'jsocr', 'jsocr_ai')
class TestOllamaService(TransactionCase):
    """Test cases for OllamaService."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Import the service
        from odoo.addons.js_invoice_ocr_ia.services.ai_service import OllamaService
        cls.OllamaService = OllamaService

    def test_service_initialization(self):
        """Test OllamaService initializes with correct defaults."""
        service = self.OllamaService()

        self.assertEqual(service.url, 'http://localhost:11434')
        self.assertEqual(service.model, 'llama3')
        self.assertEqual(service.timeout, 120)

    def test_service_custom_config(self):
        """Test OllamaService accepts custom configuration."""
        service = self.OllamaService(
            url='http://custom:8080',
            model='mistral',
            timeout=60
        )

        self.assertEqual(service.url, 'http://custom:8080')
        self.assertEqual(service.model, 'mistral')
        self.assertEqual(service.timeout, 60)

    # -------------------------------------------------------------------------
    # Story 4.1: Connection Tests
    # -------------------------------------------------------------------------

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service.requests.get')
    def test_connection_success(self, mock_get):
        """Test successful connection to Ollama."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'models': [
                {'name': 'llama3'},
                {'name': 'mistral'},
            ]
        }

        service = self.OllamaService()
        success, message, models = service.test_connection()

        self.assertTrue(success)
        self.assertIn('2 model(s)', message)
        self.assertEqual(models, ['llama3', 'mistral'])

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service.requests.get')
    def test_connection_timeout(self, mock_get):
        """Test connection timeout handling."""
        import requests
        mock_get.side_effect = requests.Timeout()

        service = self.OllamaService()
        success, message, models = service.test_connection()

        self.assertFalse(success)
        self.assertIn('timeout', message.lower())

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service.requests.get')
    def test_connection_error(self, mock_get):
        """Test connection error handling."""
        import requests
        mock_get.side_effect = requests.ConnectionError()

        service = self.OllamaService()
        success, message, models = service.test_connection()

        self.assertFalse(success)
        self.assertIn('error', message.lower())

    # -------------------------------------------------------------------------
    # Story 4.2: Prompt Building Tests
    # -------------------------------------------------------------------------

    def test_prompt_building_french(self):
        """Test prompt includes French context."""
        service = self.OllamaService()
        prompt = service._build_extraction_prompt("Test invoice text", 'fr')

        self.assertIn('francais', prompt.lower())
        self.assertIn('suisse', prompt.lower())
        self.assertIn('7.7%', prompt)

    def test_prompt_building_german(self):
        """Test prompt includes German context."""
        service = self.OllamaService()
        prompt = service._build_extraction_prompt("Test invoice text", 'de')

        self.assertIn('allemand', prompt.lower())

    def test_prompt_building_english(self):
        """Test prompt includes English context."""
        service = self.OllamaService()
        prompt = service._build_extraction_prompt("Test invoice text", 'en')

        self.assertIn('anglais', prompt.lower())

    def test_prompt_includes_invoice_text(self):
        """Test prompt includes the invoice text."""
        service = self.OllamaService()
        test_text = "UNIQUE_INVOICE_TEXT_12345"
        prompt = service._build_extraction_prompt(test_text, 'fr')

        self.assertIn(test_text, prompt)

    def test_prompt_requests_json_format(self):
        """Test prompt requests JSON output."""
        service = self.OllamaService()
        prompt = service._build_extraction_prompt("Test", 'fr')

        self.assertIn('JSON', prompt)
        self.assertIn('supplier_name', prompt)
        self.assertIn('invoice_date', prompt)
        self.assertIn('lines', prompt)

    # -------------------------------------------------------------------------
    # Story 4.3-4.6: Data Extraction Tests (via parsing)
    # -------------------------------------------------------------------------

    def test_parse_valid_json_response(self):
        """Test parsing a valid JSON response."""
        service = self.OllamaService()

        response = json.dumps({
            'supplier_name': 'Test Supplier SA',
            'invoice_date': '2026-01-15',
            'invoice_number': 'INV-001',
            'lines': [
                {'description': 'Service', 'quantity': 1, 'unit_price': 100, 'amount': 100}
            ],
            'amount_untaxed': 100,
            'amount_tax': 7.7,
            'amount_total': 107.7,
        })

        result = service._parse_ai_response(response)

        self.assertIsNotNone(result)
        self.assertEqual(result['supplier_name'], 'Test Supplier SA')
        self.assertEqual(result['invoice_date'], '2026-01-15')

    def test_parse_json_with_extra_text(self):
        """Test parsing JSON embedded in text."""
        service = self.OllamaService()

        response = """Here is the extracted data:
        {"supplier_name": "Test", "invoice_date": "2026-01-15", "invoice_number": null, "lines": [], "amount_untaxed": 0, "amount_tax": 0, "amount_total": 0}
        End of response."""

        result = service._parse_ai_response(response)

        self.assertIsNotNone(result)
        self.assertEqual(result['supplier_name'], 'Test')

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns None."""
        service = self.OllamaService()

        result = service._parse_ai_response("This is not JSON at all")

        self.assertIsNone(result)

    def test_parse_empty_response(self):
        """Test parsing empty response returns None."""
        service = self.OllamaService()

        self.assertIsNone(service._parse_ai_response(""))
        self.assertIsNone(service._parse_ai_response(None))

    # -------------------------------------------------------------------------
    # Story 4.4: Date Parsing Tests
    # -------------------------------------------------------------------------

    def test_parse_date_iso_format(self):
        """Test parsing ISO date format (YYYY-MM-DD)."""
        service = self.OllamaService()

        result = service.parse_invoice_date('2026-01-15')

        self.assertEqual(result, '2026-01-15')

    def test_parse_date_european_dot(self):
        """Test parsing European date format (DD.MM.YYYY)."""
        service = self.OllamaService()

        result = service.parse_invoice_date('15.01.2026')

        self.assertEqual(result, '2026-01-15')

    def test_parse_date_european_slash(self):
        """Test parsing European date format (DD/MM/YYYY)."""
        service = self.OllamaService()

        result = service.parse_invoice_date('15/01/2026')

        self.assertEqual(result, '2026-01-15')

    def test_parse_date_short_year(self):
        """Test parsing date with short year (DD.MM.YY)."""
        service = self.OllamaService()

        result = service.parse_invoice_date('15.01.26')

        self.assertEqual(result, '2026-01-15')

    def test_parse_date_invalid(self):
        """Test parsing invalid date returns None."""
        service = self.OllamaService()

        self.assertIsNone(service.parse_invoice_date('invalid'))
        self.assertIsNone(service.parse_invoice_date(''))
        self.assertIsNone(service.parse_invoice_date(None))

    # -------------------------------------------------------------------------
    # Story 4.5: Lines Parsing Tests
    # -------------------------------------------------------------------------

    def test_parse_lines_valid(self):
        """Test parsing valid invoice lines."""
        service = self.OllamaService()

        lines_data = [
            {'description': 'Service A', 'quantity': 2, 'unit_price': 50, 'amount': 100},
            {'description': 'Service B', 'quantity': 1, 'unit_price': 200, 'amount': 200},
        ]

        result = service.parse_invoice_lines(lines_data)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['description'], 'Service A')
        self.assertEqual(result[0]['quantity'], 2.0)
        self.assertEqual(result[0]['amount'], 100.0)

    def test_parse_lines_calculates_amount(self):
        """Test lines calculation when amount is missing."""
        service = self.OllamaService()

        lines_data = [
            {'description': 'Service', 'quantity': 3, 'unit_price': 100},  # No amount
        ]

        result = service.parse_invoice_lines(lines_data)

        self.assertEqual(result[0]['amount'], 300.0)

    def test_parse_lines_empty(self):
        """Test parsing empty lines returns empty list."""
        service = self.OllamaService()

        self.assertEqual(service.parse_invoice_lines([]), [])
        self.assertEqual(service.parse_invoice_lines(None), [])

    # -------------------------------------------------------------------------
    # Story 4.6: Amount Parsing Tests
    # -------------------------------------------------------------------------

    def test_parse_amount_float(self):
        """Test parsing float amount."""
        service = self.OllamaService()

        self.assertEqual(service._parse_amount(123.45), 123.45)

    def test_parse_amount_int(self):
        """Test parsing integer amount."""
        service = self.OllamaService()

        self.assertEqual(service._parse_amount(100), 100.0)

    def test_parse_amount_string_with_comma(self):
        """Test parsing string amount with comma decimal."""
        service = self.OllamaService()

        self.assertEqual(service._parse_amount("123,45"), 123.45)

    def test_parse_amount_string_with_apostrophe(self):
        """Test parsing string amount with Swiss thousand separator."""
        service = self.OllamaService()

        self.assertEqual(service._parse_amount("1'234.56"), 1234.56)
        self.assertEqual(service._parse_amount("1'234,56"), 1234.56)

    def test_parse_amount_none(self):
        """Test parsing None amount returns None."""
        service = self.OllamaService()

        self.assertIsNone(service._parse_amount(None))

    # -------------------------------------------------------------------------
    # Story 4.7: Confidence Calculation Tests
    # -------------------------------------------------------------------------

    def test_confidence_all_fields_present(self):
        """Test confidence when all fields are present and valid."""
        service = self.OllamaService()

        data = {
            'supplier_name': 'Test Supplier SA',
            'invoice_date': '2026-01-15',
            'invoice_number': 'INV-001',
            'lines': [
                {'description': 'Service', 'quantity': 1, 'unit_price': 100, 'amount': 100}
            ],
            'amount_untaxed': 100,
            'amount_tax': 7.7,
            'amount_total': 107.7,
        }

        confidence = service._calculate_confidence(data)

        # All fields should have non-zero confidence
        self.assertGreater(confidence['supplier']['confidence'], 0)
        self.assertGreater(confidence['date']['confidence'], 0)
        self.assertGreater(confidence['invoice_number']['confidence'], 0)
        self.assertGreater(confidence['lines']['confidence'], 0)
        self.assertGreater(confidence['amount_total']['confidence'], 0)

        # Global should be calculated
        self.assertIn('global', confidence)
        self.assertGreater(confidence['global']['confidence'], 50)

    def test_confidence_missing_supplier(self):
        """Test confidence when supplier is missing."""
        service = self.OllamaService()

        data = {
            'supplier_name': None,
            'invoice_date': '2026-01-15',
            'invoice_number': 'INV-001',
            'lines': [],
            'amount_untaxed': 100,
            'amount_tax': 7.7,
            'amount_total': 107.7,
        }

        confidence = service._calculate_confidence(data)

        self.assertEqual(confidence['supplier']['confidence'], 0)

    def test_confidence_amounts_coherent(self):
        """Test confidence when amounts are coherent (HT + TVA = TTC)."""
        service = self.OllamaService()

        data = {
            'supplier_name': 'Test',
            'invoice_date': '2026-01-15',
            'invoice_number': None,
            'lines': [],
            'amount_untaxed': 100.0,
            'amount_tax': 7.70,
            'amount_total': 107.70,
        }

        confidence = service._calculate_confidence(data)

        # Should have high confidence for coherent amounts
        self.assertGreater(confidence['amount_total']['confidence'], 80)

    def test_confidence_amounts_incoherent(self):
        """Test confidence warning when amounts don't add up."""
        service = self.OllamaService()

        data = {
            'supplier_name': 'Test',
            'invoice_date': '2026-01-15',
            'invoice_number': None,
            'lines': [],
            'amount_untaxed': 100.0,
            'amount_tax': 7.70,
            'amount_total': 200.0,  # Wrong! Should be 107.70
        }

        confidence = service._calculate_confidence(data)

        # Should have lower confidence for incoherent amounts
        self.assertLess(confidence['amount_total']['confidence'], 80)

    # -------------------------------------------------------------------------
    # Story 4.1-4.7: Full Extraction Tests
    # -------------------------------------------------------------------------

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service.requests.post')
    def test_extract_invoice_data_success(self, mock_post):
        """Test successful invoice data extraction."""
        mock_response = {
            'response': json.dumps({
                'supplier_name': 'Muller SA',
                'invoice_date': '2026-01-15',
                'invoice_number': 'F-2026-001',
                'lines': [
                    {'description': 'Consulting', 'quantity': 8, 'unit_price': 150, 'amount': 1200}
                ],
                'amount_untaxed': 1200,
                'amount_tax': 92.4,
                'amount_total': 1292.4,
            })
        }
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response

        service = self.OllamaService()
        result = service.extract_invoice_data("Sample invoice text", language='fr')

        self.assertTrue(result['success'])
        self.assertIsNotNone(result['data'])
        self.assertEqual(result['data']['supplier_name'], 'Muller SA')
        self.assertIsNotNone(result['confidence_data'])
        self.assertIsNone(result['error'])

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service.requests.post')
    def test_extract_invoice_data_timeout(self, mock_post):
        """Test timeout handling during extraction."""
        import requests
        mock_post.side_effect = requests.Timeout()

        service = self.OllamaService()
        result = service.extract_invoice_data("Sample text", language='fr')

        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'timeout')
        self.assertIn('timeout', result['error'].lower())

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service.requests.post')
    def test_extract_invoice_data_connection_error(self, mock_post):
        """Test connection error handling during extraction."""
        import requests
        mock_post.side_effect = requests.ConnectionError()

        service = self.OllamaService()
        result = service.extract_invoice_data("Sample text", language='fr')

        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'connection_error')

    def test_extract_invoice_data_empty_text(self):
        """Test extraction with empty text."""
        service = self.OllamaService()
        result = service.extract_invoice_data("", language='fr')

        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'validation_error')

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service.requests.post')
    def test_extract_invoice_data_parse_error(self, mock_post):
        """Test parse error handling when AI returns invalid JSON."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'response': 'This is not valid JSON at all, just random text!'
        }

        service = self.OllamaService()
        result = service.extract_invoice_data("Sample text", language='fr')

        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'parse_error')


@tagged('post_install', '-at_install', 'jsocr', 'jsocr_ai')
class TestSupplierMatching(TransactionCase):
    """Test cases for supplier matching (Story 4.3)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from odoo.addons.js_invoice_ocr_ia.services.ai_service import OllamaService
        cls.OllamaService = OllamaService

        # Create test partners
        cls.partner_exact = cls.env['res.partner'].create({
            'name': 'Muller AG',
            'is_company': True,
        })
        cls.partner_alias = cls.env['res.partner'].create({
            'name': 'Schneider SA',
            'is_company': True,
            'jsocr_aliases': '["Schneider Suisse", "Schneider CH"]',
        })

    def test_find_supplier_exact_match(self):
        """Test finding supplier by exact name returns (partner, 'exact')."""
        service = self.OllamaService()
        partner, match_type = service.find_supplier(self.env, 'Muller AG')

        self.assertEqual(partner, self.partner_exact)
        self.assertEqual(match_type, 'exact')

    def test_find_supplier_partial_match(self):
        """Test finding supplier by partial name returns (partner, 'partial')."""
        service = self.OllamaService()
        partner, match_type = service.find_supplier(self.env, 'Muller')

        self.assertEqual(partner, self.partner_exact)
        self.assertEqual(match_type, 'partial')

    def test_find_supplier_by_alias(self):
        """Test finding supplier by alias returns (partner, 'alias')."""
        service = self.OllamaService()
        partner, match_type = service.find_supplier(self.env, 'Schneider Suisse')

        self.assertEqual(partner, self.partner_alias)
        self.assertEqual(match_type, 'alias')

    def test_find_supplier_not_found(self):
        """Test finding non-existent supplier returns (False, None)."""
        service = self.OllamaService()
        partner, match_type = service.find_supplier(self.env, 'Unknown Company XYZ')

        self.assertFalse(partner)
        self.assertIsNone(match_type)

    def test_find_supplier_empty_name(self):
        """Test finding supplier with empty name returns (False, None)."""
        service = self.OllamaService()

        partner, match_type = service.find_supplier(self.env, '')
        self.assertFalse(partner)
        self.assertIsNone(match_type)

        partner, match_type = service.find_supplier(self.env, None)
        self.assertFalse(partner)
        self.assertIsNone(match_type)

        partner, match_type = service.find_supplier(self.env, '   ')
        self.assertFalse(partner)
        self.assertIsNone(match_type)
