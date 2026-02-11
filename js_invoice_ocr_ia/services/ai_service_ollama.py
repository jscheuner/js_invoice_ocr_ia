# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

"""Ollama AI Service provider for invoice data extraction.

Implements the AIServiceBase interface for local Ollama instances.

Epic 7 — Multi-Provider AI Abstraction
"""

import logging

import requests

from .ai_service_base import (
    AIServiceBase,
    AIServiceConnectionError,
    AIServiceError,
    AIServiceTimeoutError,
    DEFAULT_TIMEOUT,
)

_logger = logging.getLogger(__name__)


class OllamaService(AIServiceBase):
    """AI service provider for Ollama (local LLM).

    Connects to a local Ollama instance and uses LLM to extract structured
    invoice data from OCR text.

    Example usage:
        service = OllamaService(url='http://localhost:11434', model='llama3')
        result = service.extract_invoice_data(extracted_text, language='fr')
    """

    provider_name = 'ollama'

    def __init__(self, url=None, model=None, timeout=None):
        """Initialize Ollama service.

        Args:
            url (str): Ollama API URL (e.g., 'http://localhost:11434')
            model (str): Model name to use (e.g., 'llama3', 'mistral')
            timeout (int): Request timeout in seconds (default: 120)
        """
        super().__init__(model=model, timeout=timeout)
        self.url = url or 'http://localhost:11434'
        _logger.info("JSOCR: OllamaService initialized (model=%s)", self.model)

    def test_connection(self):
        """Test connection to Ollama server.

        Returns:
            tuple: (success: bool, message: str, models: list)
        """
        try:
            response = requests.get(
                f"{self.url}/api/tags",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                return True, f"Connection OK - {len(models)} model(s) available", models
            else:
                return False, f"HTTP {response.status_code}", []
        except requests.Timeout:
            return False, "Connection timeout", []
        except requests.ConnectionError:
            return False, "Connection error - server unreachable", []
        except Exception as e:
            return False, f"Error: {str(e)}", []

    def _call_api(self, prompt):
        """Send request to Ollama API and return the text response.

        Args:
            prompt (str): The prompt to send

        Returns:
            str: Raw text response from Ollama

        Raises:
            AIServiceTimeoutError: If request times out
            AIServiceConnectionError: If connection fails
            AIServiceError: For other errors
        """
        payload = {
            'model': self.model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': 0.1,
                'num_predict': 2000,
            }
        }

        _logger.info("JSOCR: Sending request to Ollama (model=%s)", self.model)

        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
        except requests.Timeout:
            raise AIServiceTimeoutError(f"Ollama timeout after {self.timeout}s")
        except requests.ConnectionError as e:
            raise AIServiceConnectionError(str(e))

        if response.status_code != 200:
            raise AIServiceError(f"Ollama returned HTTP {response.status_code}")

        return response.json().get('response', '')

    def _build_metadata(self, tokens=0, processing_time=0.0):
        """Build metadata with zero cost for local Ollama.

        Args:
            tokens (int): Number of tokens used
            processing_time (float): Processing time in seconds

        Returns:
            dict: Metadata dict
        """
        meta = super()._build_metadata(tokens=tokens, processing_time=processing_time)
        meta['cost_estimate'] = 0.0
        return meta
