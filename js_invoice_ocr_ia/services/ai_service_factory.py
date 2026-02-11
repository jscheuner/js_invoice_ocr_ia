# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

"""AI Service Factory — instantiates the correct provider from config.

Epic 7 — Multi-Provider AI Abstraction
"""

import logging

_logger = logging.getLogger(__name__)


class AIServiceFactory:
    """Factory that creates the appropriate AI service from jsocr.config."""

    @staticmethod
    def create(config):
        """Create an AI service instance based on configuration.

        Args:
            config: jsocr.config record (or object with ai_provider,
                    ollama_url, ollama_model, ollama_timeout attributes)

        Returns:
            AIServiceBase: Configured AI service instance

        Raises:
            ValueError: If the provider is not supported
        """
        provider = getattr(config, 'ai_provider', None) or 'ollama'

        if provider == 'ollama':
            from .ai_service_ollama import OllamaService
            service = OllamaService(
                url=config.ollama_url,
                model=config.ollama_model,
                timeout=config.ollama_timeout,
            )
            _logger.info("JSOCR: AI provider created: %s", provider)
            return service

        if provider == 'claude':
            from .ai_service_claude import ClaudeService
            service = ClaudeService(
                api_key=config.ai_api_key,
                url=config.ai_base_url or None,
                model=config.ai_model_name or None,
                timeout=config.ollama_timeout or None,
            )
            _logger.info("JSOCR: AI provider created: %s", provider)
            return service

        raise ValueError(
            f"Unsupported AI provider: '{provider}'. "
            f"Supported providers: ollama, claude."
        )

    @staticmethod
    def create_with_fallback(config):
        """Create an AI service with fallback support (stub).

        Currently delegates to create(). Full fallback chain will be
        implemented in Epic 9.

        Args:
            config: jsocr.config record

        Returns:
            AIServiceBase: Configured AI service instance
        """
        return AIServiceFactory.create(config)
