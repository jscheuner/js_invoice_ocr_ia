# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

"""Tests for AIServiceBase abstract class (Epic 7 — Story 7.5)."""

import json
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'jsocr', 'jsocr_ai')
class TestAIServiceBase(TransactionCase):
    """Test cases for AIServiceBase abstract class."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from odoo.addons.js_invoice_ocr_ia.services.ai_service_base import (
            AIServiceBase,
            AIServiceError,
            AIServiceTimeoutError,
            AIServiceConnectionError,
        )
        cls.AIServiceBase = AIServiceBase
        cls.AIServiceError = AIServiceError
        cls.AIServiceTimeoutError = AIServiceTimeoutError
        cls.AIServiceConnectionError = AIServiceConnectionError

        # Concrete mock implementation for testing
        class MockAIService(AIServiceBase):
            provider_name = 'mock'

            def __init__(self, model=None, timeout=None):
                super().__init__(model=model, timeout=timeout)
                self.last_prompt = None
                self.mock_response = '{}'

            def _call_api(self, prompt):
                self.last_prompt = prompt
                return self.mock_response

            def test_connection(self):
                return True, 'Mock OK', ['mock-model']

        cls.MockAIService = MockAIService

    # ------------------------------------------------------------------
    # ABC enforcement
    # ------------------------------------------------------------------

    def test_cannot_instantiate_base(self):
        """Test that AIServiceBase cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            self.AIServiceBase()

    # ------------------------------------------------------------------
    # _parse_ai_response
    # ------------------------------------------------------------------

    def test_parse_ai_response_valid_json(self):
        """Test parsing a valid JSON string."""
        service = self.MockAIService()
        data = {'supplier_name': 'Test SA', 'invoice_date': '2026-01-15'}
        result = service._parse_ai_response(json.dumps(data))

        self.assertEqual(result['supplier_name'], 'Test SA')
        self.assertEqual(result['invoice_date'], '2026-01-15')

    def test_parse_ai_response_json_in_text(self):
        """Test parsing JSON surrounded by extra text."""
        service = self.MockAIService()
        response = 'Here is the result:\n{"supplier_name": "Test"}\nDone.'
        result = service._parse_ai_response(response)

        self.assertIsNotNone(result)
        self.assertEqual(result['supplier_name'], 'Test')

    def test_parse_ai_response_empty(self):
        """Test parsing empty/None response returns None."""
        service = self.MockAIService()

        self.assertIsNone(service._parse_ai_response(''))
        self.assertIsNone(service._parse_ai_response(None))

    # ------------------------------------------------------------------
    # _build_extraction_prompt
    # ------------------------------------------------------------------

    def test_build_extraction_prompt(self):
        """Test prompt contains the invoice text and JSON schema."""
        service = self.MockAIService()
        prompt = service._build_extraction_prompt('FACTURE TEST 123', 'fr')

        self.assertIn('FACTURE TEST 123', prompt)
        self.assertIn('supplier_name', prompt)
        self.assertIn('invoice_date', prompt)
        self.assertIn('lines', prompt)
        self.assertIn('JSON', prompt)

    # ------------------------------------------------------------------
    # _calculate_confidence
    # ------------------------------------------------------------------

    def test_calculate_confidence_all_fields(self):
        """Test confidence calculation with all fields present."""
        service = self.MockAIService()
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

        self.assertGreater(confidence['supplier']['confidence'], 0)
        self.assertGreater(confidence['date']['confidence'], 0)
        self.assertGreater(confidence['invoice_number']['confidence'], 0)
        self.assertGreater(confidence['lines']['confidence'], 0)
        self.assertGreater(confidence['amount_total']['confidence'], 0)
        self.assertIn('global', confidence)
        self.assertGreater(confidence['global']['confidence'], 50)

    def test_calculate_confidence_missing_fields(self):
        """Test confidence calculation with missing fields."""
        service = self.MockAIService()
        data = {
            'supplier_name': None,
            'invoice_date': None,
            'invoice_number': None,
            'lines': [],
            'amount_untaxed': None,
            'amount_tax': None,
            'amount_total': None,
        }
        confidence = service._calculate_confidence(data)

        self.assertEqual(confidence['supplier']['confidence'], 0)
        self.assertEqual(confidence['date']['confidence'], 0)
        self.assertEqual(confidence['invoice_number']['confidence'], 0)
        self.assertEqual(confidence['lines']['confidence'], 0)
        self.assertEqual(confidence['amount_total']['confidence'], 0)
        self.assertEqual(confidence['global']['confidence'], 0)

    # ------------------------------------------------------------------
    # _build_metadata
    # ------------------------------------------------------------------

    def test_build_metadata_defaults(self):
        """Test metadata with default values."""
        service = self.MockAIService()
        meta = service._build_metadata()

        self.assertEqual(meta['provider'], 'mock')
        self.assertEqual(meta['model'], 'llama3')
        self.assertEqual(meta['tokens'], 0)
        self.assertEqual(meta['processing_time'], 0.0)
        self.assertEqual(meta['cost_estimate'], 0.0)

    def test_build_metadata_custom(self):
        """Test metadata with custom values."""
        service = self.MockAIService(model='custom-model')
        meta = service._build_metadata(tokens=500, processing_time=2.5)

        self.assertEqual(meta['provider'], 'mock')
        self.assertEqual(meta['model'], 'custom-model')
        self.assertEqual(meta['tokens'], 500)
        self.assertEqual(meta['processing_time'], 2.5)

    # ------------------------------------------------------------------
    # extract_invoice_data (template method)
    # ------------------------------------------------------------------

    def test_extract_invoice_data_via_mock(self):
        """Test that extract_invoice_data calls _call_api and parses result."""
        service = self.MockAIService()
        service.mock_response = json.dumps({
            'supplier_name': 'Mock SA',
            'invoice_date': '2026-03-01',
            'invoice_number': 'M-001',
            'lines': [{'description': 'Test', 'amount': 100}],
            'amount_untaxed': 100,
            'amount_tax': 7.7,
            'amount_total': 107.7,
        })

        result = service.extract_invoice_data('Some invoice text', language='fr')

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['supplier_name'], 'Mock SA')
        self.assertIsNotNone(result['confidence_data'])
        self.assertIn('metadata', result)
        self.assertEqual(result['metadata']['provider'], 'mock')
        # Verify the prompt was passed to _call_api
        self.assertIn('Some invoice text', service.last_prompt)

    def test_extract_invoice_data_empty_text(self):
        """Test extraction with empty text returns validation error."""
        service = self.MockAIService()
        result = service.extract_invoice_data('', language='fr')

        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'validation_error')

    def test_extract_invoice_data_timeout(self):
        """Test extraction handles AIServiceTimeoutError."""
        service = self.MockAIService()

        # Override _call_api to raise timeout
        def raise_timeout(prompt):
            raise self.AIServiceTimeoutError('timeout')
        service._call_api = raise_timeout

        result = service.extract_invoice_data('Some text', language='fr')

        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'timeout')

    def test_extract_invoice_data_connection_error(self):
        """Test extraction handles AIServiceConnectionError."""
        service = self.MockAIService()

        def raise_conn_error(prompt):
            raise self.AIServiceConnectionError('unreachable')
        service._call_api = raise_conn_error

        result = service.extract_invoice_data('Some text', language='fr')

        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'connection_error')

    # ------------------------------------------------------------------
    # Exception hierarchy
    # ------------------------------------------------------------------

    def test_exception_hierarchy(self):
        """Test that specific exceptions inherit from AIServiceError."""
        self.assertTrue(issubclass(self.AIServiceTimeoutError, self.AIServiceError))
        self.assertTrue(issubclass(self.AIServiceConnectionError, self.AIServiceError))
