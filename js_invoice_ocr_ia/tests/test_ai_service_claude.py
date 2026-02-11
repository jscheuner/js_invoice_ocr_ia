# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

"""Tests for ClaudeService (Epic 8 — Claude AI Provider)."""

import json
from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'jsocr', 'jsocr_claude')
class TestClaudeServiceProvider(TransactionCase):
    """Test cases for ClaudeService."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from odoo.addons.js_invoice_ocr_ia.services.ai_service_claude import (
            ClaudeService,
            AIServiceAuthenticationError,
            AIServiceRateLimitError,
            CLAUDE_PRICING,
            DEFAULT_CLAUDE_MODEL,
            DEFAULT_CLAUDE_URL,
            DEFAULT_MAX_TOKENS,
        )
        from odoo.addons.js_invoice_ocr_ia.services.ai_service_base import (
            AIServiceBase,
            AIServiceError,
            AIServiceTimeoutError,
            AIServiceConnectionError,
        )
        cls.ClaudeService = ClaudeService
        cls.AIServiceBase = AIServiceBase
        cls.AIServiceError = AIServiceError
        cls.AIServiceTimeoutError = AIServiceTimeoutError
        cls.AIServiceConnectionError = AIServiceConnectionError
        cls.AIServiceAuthenticationError = AIServiceAuthenticationError
        cls.AIServiceRateLimitError = AIServiceRateLimitError
        cls.CLAUDE_PRICING = CLAUDE_PRICING
        cls.DEFAULT_CLAUDE_MODEL = DEFAULT_CLAUDE_MODEL
        cls.DEFAULT_CLAUDE_URL = DEFAULT_CLAUDE_URL
        cls.DEFAULT_MAX_TOKENS = DEFAULT_MAX_TOKENS

    def _make_service(self, **kwargs):
        """Create a ClaudeService with test defaults."""
        return self.ClaudeService(
            api_key=kwargs.get('api_key', 'sk-ant-test-key'),
            url=kwargs.get('url'),
            model=kwargs.get('model'),
            timeout=kwargs.get('timeout'),
        )

    def _mock_response(self, status_code=200, json_data=None):
        """Create a mock requests.Response."""
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data or {}
        return resp

    # ------------------------------------------------------------------
    # Heritage / Identity
    # ------------------------------------------------------------------

    def test_inherits_from_base(self):
        """ClaudeService inherits from AIServiceBase."""
        service = self._make_service()
        self.assertIsInstance(service, self.AIServiceBase)

    def test_provider_name(self):
        """Provider name is 'claude'."""
        service = self._make_service()
        self.assertEqual(service.provider_name, 'claude')

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def test_init_defaults(self):
        """Defaults are applied when no args provided."""
        service = self.ClaudeService(api_key='key')
        self.assertEqual(service.model, self.DEFAULT_CLAUDE_MODEL)
        self.assertEqual(service.url, self.DEFAULT_CLAUDE_URL)
        self.assertEqual(service.timeout, 120)
        self.assertEqual(service.api_key, 'key')

    def test_init_custom(self):
        """Custom values are stored correctly."""
        service = self.ClaudeService(
            api_key='my-key',
            url='https://custom.api.com',
            model='claude-haiku-4-5-20251001',
            timeout=60,
        )
        self.assertEqual(service.api_key, 'my-key')
        self.assertEqual(service.url, 'https://custom.api.com')
        self.assertEqual(service.model, 'claude-haiku-4-5-20251001')
        self.assertEqual(service.timeout, 60)

    # ------------------------------------------------------------------
    # _call_api
    # ------------------------------------------------------------------

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_claude.requests.post')
    def test_call_api_success(self, mock_post):
        """Successful API call returns extracted text."""
        mock_post.return_value = self._mock_response(200, {
            'content': [{'type': 'text', 'text': '{"supplier_name": "Test"}'}],
            'usage': {'input_tokens': 100, 'output_tokens': 50},
        })
        service = self._make_service()
        result = service._call_api('Extract this invoice')
        self.assertEqual(result, '{"supplier_name": "Test"}')

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_claude.requests.post')
    def test_call_api_timeout(self, mock_post):
        """Timeout raises AIServiceTimeoutError."""
        import requests as req
        mock_post.side_effect = req.Timeout()
        service = self._make_service()
        with self.assertRaises(self.AIServiceTimeoutError):
            service._call_api('prompt')

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_claude.requests.post')
    def test_call_api_connection_error(self, mock_post):
        """Connection error raises AIServiceConnectionError."""
        import requests as req
        mock_post.side_effect = req.ConnectionError('refused')
        service = self._make_service()
        with self.assertRaises(self.AIServiceConnectionError):
            service._call_api('prompt')

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_claude.requests.post')
    def test_call_api_auth_401(self, mock_post):
        """HTTP 401 raises AIServiceAuthenticationError."""
        mock_post.return_value = self._mock_response(401, {
            'type': 'error',
            'error': {'type': 'authentication_error', 'message': 'invalid api key'},
        })
        service = self._make_service()
        with self.assertRaises(self.AIServiceAuthenticationError):
            service._call_api('prompt')

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_claude.requests.post')
    def test_call_api_rate_limit_429(self, mock_post):
        """HTTP 429 raises AIServiceRateLimitError."""
        mock_post.return_value = self._mock_response(429, {
            'type': 'error',
            'error': {'type': 'rate_limit_error', 'message': 'too many requests'},
        })
        service = self._make_service()
        with self.assertRaises(self.AIServiceRateLimitError):
            service._call_api('prompt')

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_claude.requests.post')
    def test_call_api_server_500(self, mock_post):
        """HTTP 500 raises AIServiceError."""
        mock_post.return_value = self._mock_response(500, {
            'type': 'error',
            'error': {'type': 'api_error', 'message': 'internal error'},
        })
        service = self._make_service()
        with self.assertRaises(self.AIServiceError):
            service._call_api('prompt')

    def test_call_api_no_api_key(self):
        """Missing API key raises AIServiceAuthenticationError."""
        service = self.ClaudeService(api_key=None)
        with self.assertRaises(self.AIServiceAuthenticationError):
            service._call_api('prompt')

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_claude.requests.post')
    def test_call_api_correct_payload(self, mock_post):
        """Payload sent to API has correct structure."""
        mock_post.return_value = self._mock_response(200, {
            'content': [{'type': 'text', 'text': 'ok'}],
            'usage': {'input_tokens': 10, 'output_tokens': 5},
        })
        service = self._make_service(model='claude-haiku-4-5-20251001')
        service._call_api('test prompt')

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get('json') or call_kwargs[1].get('json')
        self.assertEqual(payload['model'], 'claude-haiku-4-5-20251001')
        self.assertEqual(payload['max_tokens'], self.DEFAULT_MAX_TOKENS)
        self.assertEqual(payload['messages'][0]['role'], 'user')
        self.assertEqual(payload['messages'][0]['content'], 'test prompt')

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_claude.requests.post')
    def test_call_api_correct_headers(self, mock_post):
        """Headers include API key and Anthropic version."""
        mock_post.return_value = self._mock_response(200, {
            'content': [{'type': 'text', 'text': 'ok'}],
            'usage': {'input_tokens': 0, 'output_tokens': 0},
        })
        service = self._make_service(api_key='sk-ant-test-123')
        service._call_api('prompt')

        call_kwargs = mock_post.call_args
        headers = call_kwargs.kwargs.get('headers') or call_kwargs[1].get('headers')
        self.assertEqual(headers['x-api-key'], 'sk-ant-test-123')
        self.assertEqual(headers['anthropic-version'], '2023-06-01')
        self.assertEqual(headers['content-type'], 'application/json')

    # ------------------------------------------------------------------
    # test_connection
    # ------------------------------------------------------------------

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_claude.requests.post')
    def test_test_connection_success(self, mock_post):
        """Successful connection returns (True, message, [model])."""
        mock_post.return_value = self._mock_response(200, {'input_tokens': 5})
        service = self._make_service()
        success, message, models = service.test_connection()
        self.assertTrue(success)
        self.assertIn('OK', message)
        self.assertEqual(models, [service.model])

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_claude.requests.post')
    def test_test_connection_auth_failure(self, mock_post):
        """Authentication failure returns (False, message, [])."""
        mock_post.return_value = self._mock_response(401, {
            'type': 'error',
            'error': {'type': 'authentication_error', 'message': 'invalid key'},
        })
        service = self._make_service()
        success, message, models = service.test_connection()
        self.assertFalse(success)
        self.assertIn('Authentication', message)
        self.assertEqual(models, [])

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_claude.requests.post')
    def test_test_connection_timeout(self, mock_post):
        """Timeout returns (False, message, [])."""
        import requests as req
        mock_post.side_effect = req.Timeout()
        service = self._make_service()
        success, message, models = service.test_connection()
        self.assertFalse(success)
        self.assertIn('timeout', message.lower())
        self.assertEqual(models, [])

    def test_test_connection_no_key(self):
        """Missing API key returns (False, message, [])."""
        service = self.ClaudeService(api_key=None)
        success, message, models = service.test_connection()
        self.assertFalse(success)
        self.assertIn('API key', message)
        self.assertEqual(models, [])

    # ------------------------------------------------------------------
    # Metadata / Cost calculation
    # ------------------------------------------------------------------

    def test_metadata_cost_calculation(self):
        """Cost is computed from token usage and pricing table."""
        service = self._make_service()
        service._last_usage = {'input_tokens': 1000, 'output_tokens': 500}
        meta = service._build_metadata()

        # Sonnet: $3/MTok input, $15/MTok output
        expected = (1000 / 1_000_000 * 3.0) + (500 / 1_000_000 * 15.0)
        self.assertAlmostEqual(meta['cost_estimate'], round(expected, 6))

    def test_metadata_provider_name(self):
        """Metadata includes provider='claude'."""
        service = self._make_service()
        meta = service._build_metadata()
        self.assertEqual(meta['provider'], 'claude')

    def test_metadata_unknown_model_default_pricing(self):
        """Unknown model uses default pricing."""
        service = self._make_service(model='claude-future-model')
        service._last_usage = {'input_tokens': 1_000_000, 'output_tokens': 1_000_000}
        meta = service._build_metadata()
        # Default pricing: $3 input + $15 output = $18
        self.assertAlmostEqual(meta['cost_estimate'], 18.0)

    def test_metadata_token_breakdown(self):
        """Metadata includes input_tokens and output_tokens."""
        service = self._make_service()
        service._last_usage = {'input_tokens': 200, 'output_tokens': 100}
        meta = service._build_metadata()
        self.assertEqual(meta['input_tokens'], 200)
        self.assertEqual(meta['output_tokens'], 100)
        self.assertEqual(meta['tokens'], 300)

    # ------------------------------------------------------------------
    # End-to-end extraction
    # ------------------------------------------------------------------

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_claude.requests.post')
    def test_extract_invoice_data_success(self, mock_post):
        """Full extraction pipeline works with Claude."""
        invoice_json = json.dumps({
            'supplier_name': 'Acme SA',
            'invoice_date': '2025-01-15',
            'invoice_number': 'F-2025-001',
            'lines': [{'description': 'Service', 'quantity': 1, 'unit_price': 100, 'amount': 100}],
            'amount_untaxed': 100.0,
            'amount_tax': 7.70,
            'amount_total': 107.70,
            'currency': 'CHF',
            'payment_reference': None,
        })
        mock_post.return_value = self._mock_response(200, {
            'content': [{'type': 'text', 'text': invoice_json}],
            'usage': {'input_tokens': 500, 'output_tokens': 200},
        })
        service = self._make_service()
        result = service.extract_invoice_data('Facture Acme SA...', language='fr')
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['supplier_name'], 'Acme SA')
        self.assertIn('metadata', result)
        self.assertEqual(result['metadata']['provider'], 'claude')

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_claude.requests.post')
    def test_auth_error_propagation(self, mock_post):
        """Authentication error is caught by extract_invoice_data."""
        mock_post.return_value = self._mock_response(401, {
            'type': 'error',
            'error': {'type': 'authentication_error', 'message': 'invalid key'},
        })
        service = self._make_service()
        result = service.extract_invoice_data('Some text')
        # AIServiceAuthenticationError inherits from AIServiceError,
        # which is caught as 'request_error' in extract_invoice_data
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'request_error')
