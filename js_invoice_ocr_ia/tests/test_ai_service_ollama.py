# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

"""Tests for OllamaService provider (Epic 7 — Story 7.5)."""

from unittest.mock import patch, MagicMock

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'jsocr', 'jsocr_ai')
class TestOllamaServiceProvider(TransactionCase):
    """Test cases for OllamaService as AIServiceBase implementation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from odoo.addons.js_invoice_ocr_ia.services.ai_service_ollama import OllamaService
        from odoo.addons.js_invoice_ocr_ia.services.ai_service_base import AIServiceBase
        cls.OllamaService = OllamaService
        cls.AIServiceBase = AIServiceBase

    # ------------------------------------------------------------------
    # Inheritance & identity
    # ------------------------------------------------------------------

    def test_inherits_from_base(self):
        """Test that OllamaService is an instance of AIServiceBase."""
        service = self.OllamaService()
        self.assertIsInstance(service, self.AIServiceBase)

    def test_provider_name(self):
        """Test that provider_name is 'ollama'."""
        service = self.OllamaService()
        self.assertEqual(service.provider_name, 'ollama')

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def test_initialization_defaults(self):
        """Test OllamaService initializes with correct defaults."""
        service = self.OllamaService()

        self.assertEqual(service.url, 'http://localhost:11434')
        self.assertEqual(service.model, 'llama3')
        self.assertEqual(service.timeout, 120)

    def test_initialization_custom(self):
        """Test OllamaService accepts custom configuration."""
        service = self.OllamaService(
            url='http://custom:8080',
            model='mistral',
            timeout=60
        )

        self.assertEqual(service.url, 'http://custom:8080')
        self.assertEqual(service.model, 'mistral')
        self.assertEqual(service.timeout, 60)

    # ------------------------------------------------------------------
    # _call_api
    # ------------------------------------------------------------------

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_ollama.requests.post')
    def test_call_api_success(self, mock_post):
        """Test _call_api returns response text on success."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'response': '{"supplier_name": "Test"}'
        }

        service = self.OllamaService()
        result = service._call_api('test prompt')

        self.assertEqual(result, '{"supplier_name": "Test"}')
        mock_post.assert_called_once()

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_ollama.requests.post')
    def test_call_api_timeout(self, mock_post):
        """Test _call_api raises AIServiceTimeoutError on timeout."""
        import requests
        mock_post.side_effect = requests.Timeout()

        from odoo.addons.js_invoice_ocr_ia.services.ai_service_base import AIServiceTimeoutError

        service = self.OllamaService()
        with self.assertRaises(AIServiceTimeoutError):
            service._call_api('test prompt')

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_ollama.requests.post')
    def test_call_api_connection_error(self, mock_post):
        """Test _call_api raises AIServiceConnectionError on connection failure."""
        import requests
        mock_post.side_effect = requests.ConnectionError()

        from odoo.addons.js_invoice_ocr_ia.services.ai_service_base import AIServiceConnectionError

        service = self.OllamaService()
        with self.assertRaises(AIServiceConnectionError):
            service._call_api('test prompt')

    # ------------------------------------------------------------------
    # test_connection
    # ------------------------------------------------------------------

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_ollama.requests.get')
    def test_test_connection_success(self, mock_get):
        """Test successful connection returns models list."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'models': [{'name': 'llama3'}, {'name': 'mistral'}]
        }

        service = self.OllamaService()
        success, message, models = service.test_connection()

        self.assertTrue(success)
        self.assertIn('2 model(s)', message)
        self.assertEqual(models, ['llama3', 'mistral'])

    @patch('odoo.addons.js_invoice_ocr_ia.services.ai_service_ollama.requests.get')
    def test_test_connection_failure(self, mock_get):
        """Test connection failure returns error."""
        import requests
        mock_get.side_effect = requests.ConnectionError()

        service = self.OllamaService()
        success, message, models = service.test_connection()

        self.assertFalse(success)
        self.assertIn('error', message.lower())
        self.assertEqual(models, [])

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def test_metadata_cost_zero(self):
        """Test that Ollama metadata always has cost_estimate=0."""
        service = self.OllamaService()
        meta = service._build_metadata(tokens=1000, processing_time=5.0)

        self.assertEqual(meta['cost_estimate'], 0.0)
        self.assertEqual(meta['provider'], 'ollama')
        self.assertEqual(meta['tokens'], 1000)
        self.assertEqual(meta['processing_time'], 5.0)
