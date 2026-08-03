# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

"""Claude (Anthropic) AI Service provider for invoice data extraction.

Implements the AIServiceBase interface for the Anthropic Messages API.
Uses direct HTTP requests (no SDK dependency).

Epic 8 — Claude AI Provider Integration
"""

import logging
import time

import requests

from .ai_service_base import (
    AIServiceBase,
    AIServiceConnectionError,
    AIServiceError,
    AIServiceTimeoutError,
    DEFAULT_TIMEOUT,
)

_logger = logging.getLogger(__name__)

# Defaults
DEFAULT_CLAUDE_URL = 'https://api.anthropic.com'
DEFAULT_CLAUDE_MODEL = 'claude-sonnet-4-5-20250929'
ANTHROPIC_VERSION = '2023-06-01'
DEFAULT_MAX_TOKENS = 4096

# Pricing per million tokens (input_cost, output_cost) in USD
CLAUDE_PRICING = {
    'claude-sonnet-4-5-20250929': {'input': 3.0, 'output': 15.0},
    'claude-haiku-4-5-20251001': {'input': 1.0, 'output': 5.0},
    'claude-opus-4-6': {'input': 5.0, 'output': 25.0},
}
# Fallback pricing for unknown models
DEFAULT_PRICING = {'input': 3.0, 'output': 15.0}


class AIServiceAuthenticationError(AIServiceError):
    """Raised when the API key is invalid or missing."""


class AIServiceRateLimitError(AIServiceError):
    """Raised when the API rate limit is exceeded."""


class ClaudeService(AIServiceBase):
    """AI service provider for Claude (Anthropic).

    Connects to the Anthropic Messages API and uses Claude to extract
    structured invoice data from OCR text.

    Example usage:
        service = ClaudeService(api_key='sk-ant-...', model='claude-sonnet-4-5-20250929')
        result = service.extract_invoice_data(extracted_text, language='fr')
    """

    provider_name = 'claude'

    def __init__(self, api_key=None, url=None, model=None, timeout=None):
        """Initialize Claude service.

        Args:
            api_key (str): Anthropic API key
            url (str): API base URL (default: https://api.anthropic.com)
            model (str): Model name (default: claude-sonnet-4-5-20250929)
            timeout (int): Request timeout in seconds (default: 120)
        """
        super().__init__(model=model or DEFAULT_CLAUDE_MODEL, timeout=timeout)
        self.api_key = api_key
        self.url = url or DEFAULT_CLAUDE_URL
        self._last_usage = None
        self._last_processing_time = 0.0
        _logger.info("JSOCR: ClaudeService initialized (model=%s)", self.model)

    def _get_headers(self):
        """Build HTTP headers for Anthropic API requests.

        Returns:
            dict: Headers with API key, version, and content type
        """
        return {
            'x-api-key': self.api_key or '',
            'anthropic-version': ANTHROPIC_VERSION,
            'content-type': 'application/json',
        }

    def _extract_error_message(self, response):
        """Extract error message from an Anthropic API error response.

        Anthropic error format: {"type": "error", "error": {"type": "...", "message": "..."}}

        Args:
            response: requests.Response object

        Returns:
            str: Human-readable error message
        """
        try:
            data = response.json()
            error = data.get('error', {})
            if isinstance(error, dict):
                return error.get('message', f'HTTP {response.status_code}')
            return str(error)
        except (ValueError, AttributeError):
            return f'HTTP {response.status_code}'

    def _call_api(self, prompt):
        """Send request to Anthropic Messages API and return the text response.

        Args:
            prompt (str): The prompt to send

        Returns:
            str: Raw text response from Claude

        Raises:
            AIServiceAuthenticationError: If API key is invalid (401)
            AIServiceRateLimitError: If rate limit exceeded (429)
            AIServiceTimeoutError: If request times out
            AIServiceConnectionError: If connection fails
            AIServiceError: For other errors
        """
        if not self.api_key:
            raise AIServiceAuthenticationError("API key is required for Claude provider")

        payload = {
            'model': self.model,
            'max_tokens': DEFAULT_MAX_TOKENS,
            'messages': [
                {'role': 'user', 'content': prompt},
            ],
        }

        _logger.info("JSOCR: Sending request to Claude (model=%s)", self.model)

        start_time = time.time()

        try:
            response = requests.post(
                f"{self.url}/v1/messages",
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout,
            )
        except requests.Timeout:
            raise AIServiceTimeoutError(f"Claude timeout after {self.timeout}s")
        except requests.ConnectionError as e:
            raise AIServiceConnectionError(str(e))

        self._last_processing_time = time.time() - start_time

        if response.status_code == 401:
            msg = self._extract_error_message(response)
            raise AIServiceAuthenticationError(f"Authentication failed: {msg}")

        if response.status_code == 429:
            msg = self._extract_error_message(response)
            raise AIServiceRateLimitError(f"Rate limit exceeded: {msg}")

        if response.status_code >= 500:
            msg = self._extract_error_message(response)
            raise AIServiceError(f"Claude server error ({response.status_code}): {msg}")

        if response.status_code != 200:
            msg = self._extract_error_message(response)
            raise AIServiceError(f"Claude returned HTTP {response.status_code}: {msg}")

        data = response.json()
        self._last_usage = data.get('usage')

        # Extract text from content blocks
        content = data.get('content', [])
        if content and isinstance(content, list):
            text_parts = [
                block.get('text', '')
                for block in content
                if block.get('type') == 'text'
            ]
            return ''.join(text_parts)

        return ''

    def test_connection(self):
        """Test connection to Anthropic API using the count_tokens endpoint.

        Uses POST /v1/messages/count_tokens which validates the API key
        without generating tokens (lightweight check).

        Returns:
            tuple: (success: bool, message: str, models: list)
        """
        if not self.api_key:
            return False, "API key is required", []

        try:
            payload = {
                'model': self.model,
                'messages': [
                    {'role': 'user', 'content': 'test'},
                ],
            }
            response = requests.post(
                f"{self.url}/v1/messages/count_tokens",
                headers=self._get_headers(),
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                return True, "Connection OK", [self.model]

            if response.status_code == 401:
                msg = self._extract_error_message(response)
                return False, f"Authentication failed: {msg}", []

            msg = self._extract_error_message(response)
            return False, f"HTTP {response.status_code}: {msg}", []

        except requests.Timeout:
            return False, "Connection timeout", []
        except requests.ConnectionError:
            return False, "Connection error - server unreachable", []
        except Exception as e:
            return False, f"Error: {str(e)}", []

    def _build_metadata(self, tokens=0, processing_time=0.0):
        """Build metadata with cost calculated from token usage.

        Uses actual token counts from the last API call and pricing table
        to compute a real cost estimate.

        Args:
            tokens (int): Fallback token count (overridden by actual usage)
            processing_time (float): Fallback processing time

        Returns:
            dict: Metadata with provider, model, tokens, cost_estimate, etc.
        """
        meta = super()._build_metadata(tokens=tokens, processing_time=processing_time)

        # Use actual usage data if available
        if self._last_usage:
            input_tokens = self._last_usage.get('input_tokens', 0)
            output_tokens = self._last_usage.get('output_tokens', 0)
            meta['tokens'] = input_tokens + output_tokens
            meta['input_tokens'] = input_tokens
            meta['output_tokens'] = output_tokens
        else:
            meta['input_tokens'] = 0
            meta['output_tokens'] = 0

        # Calculate cost from pricing table
        pricing = CLAUDE_PRICING.get(self.model, DEFAULT_PRICING)
        input_cost = meta['input_tokens'] / 1_000_000 * pricing['input']
        output_cost = meta['output_tokens'] / 1_000_000 * pricing['output']
        meta['cost_estimate'] = round(input_cost + output_cost, 6)

        # Use actual processing time if available
        if self._last_processing_time > 0:
            meta['processing_time'] = round(self._last_processing_time, 2)

        return meta
