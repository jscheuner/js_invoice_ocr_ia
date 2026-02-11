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
        from odoo.addons.js_invoice_ocr_ia.services.ai_service_claude import ClaudeService
        from odoo.addons.js_invoice_ocr_ia.services.ai_service_base import AIServiceBase
        cls.AIServiceFactory = AIServiceFactory
        cls.OllamaService = OllamaService
        cls.ClaudeService = ClaudeService
        cls.AIServiceBase = AIServiceBase

    def _make_config(self, **kwargs):
        """Create a mock config object."""
        config = MagicMock()
        config.ai_provider = kwargs.get('ai_provider', 'ollama')
        config.ollama_url = kwargs.get('ollama_url', 'http://localhost:11434')
        config.ollama_model = kwargs.get('ollama_model', 'llama3')
        config.ollama_timeout = kwargs.get('ollama_timeout', 120)
        config.ai_api_key = kwargs.get('ai_api_key', None)
        config.ai_base_url = kwargs.get('ai_base_url', None)
        config.ai_model_name = kwargs.get('ai_model_name', None)
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

    # ------------------------------------------------------------------
    # Claude provider (Epic 8)
    # ------------------------------------------------------------------

    def test_create_claude(self):
        """Test factory creates ClaudeService for 'claude' provider."""
        config = self._make_config(
            ai_provider='claude',
            ai_api_key='sk-ant-test',
        )
        service = self.AIServiceFactory.create(config)
        self.assertIsInstance(service, self.ClaudeService)

    def test_passes_claude_config(self):
        """Test factory passes api_key/url/model/timeout to ClaudeService."""
        config = self._make_config(
            ai_provider='claude',
            ai_api_key='sk-ant-key-123',
            ai_base_url='https://custom.anthropic.com',
            ai_model_name='claude-haiku-4-5-20251001',
            ollama_timeout=90,
        )
        service = self.AIServiceFactory.create(config)

        self.assertEqual(service.api_key, 'sk-ant-key-123')
        self.assertEqual(service.url, 'https://custom.anthropic.com')
        self.assertEqual(service.model, 'claude-haiku-4-5-20251001')
        self.assertEqual(service.timeout, 90)

    def test_claude_default_model_when_empty(self):
        """Test Claude uses default model when ai_model_name is empty."""
        config = self._make_config(
            ai_provider='claude',
            ai_api_key='sk-ant-test',
            ai_model_name='',
        )
        service = self.AIServiceFactory.create(config)
        from odoo.addons.js_invoice_ocr_ia.services.ai_service_claude import DEFAULT_CLAUDE_MODEL
        self.assertEqual(service.model, DEFAULT_CLAUDE_MODEL)

    def test_claude_default_url_when_empty(self):
        """Test Claude uses default URL when ai_base_url is empty."""
        config = self._make_config(
            ai_provider='claude',
            ai_api_key='sk-ant-test',
            ai_base_url='',
        )
        service = self.AIServiceFactory.create(config)
        from odoo.addons.js_invoice_ocr_ia.services.ai_service_claude import DEFAULT_CLAUDE_URL
        self.assertEqual(service.url, DEFAULT_CLAUDE_URL)
