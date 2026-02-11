# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

"""Tests for AIServiceFactory (Epic 7 — Story 7.5)."""

from unittest.mock import MagicMock

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'jsocr', 'jsocr_ai')
class TestAIServiceFactory(TransactionCase):
    """Test cases for AIServiceFactory."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from odoo.addons.js_invoice_ocr_ia.services.ai_service_factory import AIServiceFactory
        from odoo.addons.js_invoice_ocr_ia.services.ai_service_ollama import OllamaService
        from odoo.addons.js_invoice_ocr_ia.services.ai_service_base import AIServiceBase
        cls.AIServiceFactory = AIServiceFactory
        cls.OllamaService = OllamaService
        cls.AIServiceBase = AIServiceBase

    def _make_config(self, **kwargs):
        """Create a mock config object."""
        config = MagicMock()
        config.ai_provider = kwargs.get('ai_provider', 'ollama')
        config.ollama_url = kwargs.get('ollama_url', 'http://localhost:11434')
        config.ollama_model = kwargs.get('ollama_model', 'llama3')
        config.ollama_timeout = kwargs.get('ollama_timeout', 120)
        return config

    # ------------------------------------------------------------------
    # create()
    # ------------------------------------------------------------------

    def test_create_ollama(self):
        """Test factory creates OllamaService for 'ollama' provider."""
        config = self._make_config(ai_provider='ollama')
        service = self.AIServiceFactory.create(config)

        self.assertIsInstance(service, self.OllamaService)

    def test_create_default_ollama(self):
        """Test factory defaults to Ollama when ai_provider is empty."""
        config = self._make_config()
        config.ai_provider = None
        service = self.AIServiceFactory.create(config)

        self.assertIsInstance(service, self.OllamaService)

    def test_create_default_ollama_empty_string(self):
        """Test factory defaults to Ollama when ai_provider is empty string."""
        config = self._make_config()
        config.ai_provider = ''
        service = self.AIServiceFactory.create(config)

        self.assertIsInstance(service, self.OllamaService)

    def test_create_unsupported_raises(self):
        """Test factory raises ValueError for unsupported provider."""
        config = self._make_config(ai_provider='unsupported')
        with self.assertRaises(ValueError):
            self.AIServiceFactory.create(config)

    def test_passes_ollama_config(self):
        """Test factory passes url/model/timeout to OllamaService."""
        config = self._make_config(
            ollama_url='http://gpu:11434',
            ollama_model='mistral',
            ollama_timeout=60,
        )
        service = self.AIServiceFactory.create(config)

        self.assertEqual(service.url, 'http://gpu:11434')
        self.assertEqual(service.model, 'mistral')
        self.assertEqual(service.timeout, 60)

    # ------------------------------------------------------------------
    # create_with_fallback()
    # ------------------------------------------------------------------

    def test_create_with_fallback(self):
        """Test create_with_fallback returns a valid service (stub)."""
        config = self._make_config()
        service = self.AIServiceFactory.create_with_fallback(config)

        self.assertIsInstance(service, self.AIServiceBase)
        self.assertIsInstance(service, self.OllamaService)

    # ------------------------------------------------------------------
    # Shared methods available on created service
    # ------------------------------------------------------------------

    def test_shared_methods_available(self):
        """Test that services created by factory have all shared methods."""
        config = self._make_config()
        service = self.AIServiceFactory.create(config)

        self.assertTrue(hasattr(service, 'find_supplier'))
        self.assertTrue(hasattr(service, 'parse_invoice_date'))
        self.assertTrue(hasattr(service, 'parse_invoice_lines'))
        self.assertTrue(hasattr(service, '_parse_amount'))
        self.assertTrue(hasattr(service, 'extract_invoice_data'))
        self.assertTrue(hasattr(service, '_build_extraction_prompt'))
        self.assertTrue(hasattr(service, '_calculate_confidence'))
