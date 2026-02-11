# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

"""Abstract base class for AI services used in invoice data extraction.

Provides common parsing, confidence calculation, and extraction logic.
Concrete providers (Ollama, Claude, OpenAI) implement _call_api() and
test_connection().

Epic 7 — Multi-Provider AI Abstraction
"""

import abc
import json
import logging
import re
from datetime import datetime

_logger = logging.getLogger(__name__)

# Retry configuration (from architecture.md)
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]  # seconds

# Default timeout for AI requests (NFR1: < 2 minutes)
DEFAULT_TIMEOUT = 120


class AIServiceError(Exception):
    """Base exception for AI service errors."""


class AIServiceTimeoutError(AIServiceError):
    """Raised when an AI service request times out."""


class AIServiceConnectionError(AIServiceError):
    """Raised when the AI service is unreachable."""


class AIServiceBase(abc.ABC):
    """Abstract base class for AI-powered invoice data extraction.

    Subclasses must implement:
        - _call_api(prompt) -> str
        - test_connection() -> tuple

    Provides concrete methods for prompt building, response parsing,
    confidence calculation, supplier matching, date/line parsing.
    """

    provider_name = 'base'

    # Swiss VAT rates for validation
    SWISS_VAT_RATES = [7.7, 2.5, 0.0]

    # Date format patterns for parsing
    DATE_PATTERNS = [
        # European formats (DD.MM.YYYY, DD/MM/YYYY)
        (r'(\d{1,2})[./](\d{1,2})[./](\d{4})', 'dmy'),
        (r'(\d{1,2})[./](\d{1,2})[./](\d{2})', 'dmy_short'),
        # ISO format (YYYY-MM-DD)
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', 'ymd'),
        # Text month formats
        (r'(\d{1,2})\s+(janvier|february|fevrier|mars|april|avril|mai|may|juin|june|'
         r'juillet|july|aout|august|septembre|september|octobre|october|'
         r'novembre|november|decembre|december)\s+(\d{4})', 'text'),
    ]

    def __init__(self, model=None, timeout=None):
        """Initialize AI service.

        Args:
            model (str): Model name to use
            timeout (int): Request timeout in seconds (default: 120)
        """
        self.model = model or 'llama3'
        self.timeout = timeout or DEFAULT_TIMEOUT

    # ------------------------------------------------------------------
    # Abstract methods — must be implemented by each provider
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def _call_api(self, prompt):
        """Send a prompt to the AI provider and return the raw text response.

        Args:
            prompt (str): The prompt to send

        Returns:
            str: Raw text response from the AI

        Raises:
            AIServiceTimeoutError: If the request times out
            AIServiceConnectionError: If the service is unreachable
            AIServiceError: For other AI service errors
        """

    @abc.abstractmethod
    def test_connection(self):
        """Test the connection to the AI service.

        Returns:
            tuple: (success: bool, message: str, models: list)
        """

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def _build_metadata(self, tokens=0, processing_time=0.0):
        """Build metadata dict for the extraction result.

        Args:
            tokens (int): Number of tokens used
            processing_time (float): Processing time in seconds

        Returns:
            dict: Metadata with provider, model, tokens, processing_time, cost_estimate
        """
        return {
            'provider': self.provider_name,
            'model': self.model,
            'tokens': tokens,
            'processing_time': processing_time,
            'cost_estimate': 0.0,
        }

    # ------------------------------------------------------------------
    # Extraction (template method)
    # ------------------------------------------------------------------

    def extract_invoice_data(self, text, language='fr'):
        """Extract structured invoice data from OCR text using AI.

        Sends the text to the AI provider with a specialized prompt to extract:
        - supplier_name, invoice_date, invoice_number
        - lines (description, quantity, unit_price, amount)
        - amount_untaxed, amount_tax, amount_total

        Args:
            text (str): Extracted text from invoice PDF
            language (str): Detected language ('fr', 'de', 'en')

        Returns:
            dict: Extracted data with keys: success, data, confidence_data,
                  raw_response, error, error_type, metadata
        """
        if not text or not text.strip():
            return {
                'success': False,
                'data': None,
                'confidence_data': None,
                'raw_response': '',
                'error': 'Empty or missing text',
                'error_type': 'validation_error',
            }

        _logger.info("JSOCR: Starting AI extraction (lang=%s)", language)

        prompt = self._build_extraction_prompt(text, language)

        try:
            raw_response = self._call_api(prompt)
        except AIServiceTimeoutError:
            _logger.warning("JSOCR: AI request timeout after %ds", self.timeout)
            return {
                'success': False,
                'data': None,
                'confidence_data': None,
                'raw_response': '',
                'error': f'AI timeout after {self.timeout}s',
                'error_type': 'timeout',
            }
        except AIServiceConnectionError as e:
            _logger.error("JSOCR: AI connection error")
            return {
                'success': False,
                'data': None,
                'confidence_data': None,
                'raw_response': '',
                'error': f'Connection error: {str(e)}',
                'error_type': 'connection_error',
            }
        except AIServiceError as e:
            _logger.error("JSOCR: AI request failed: %s", type(e).__name__)
            return {
                'success': False,
                'data': None,
                'confidence_data': None,
                'raw_response': '',
                'error': f'Request error: {str(e)}',
                'error_type': 'request_error',
            }

        parsed_data = self._parse_ai_response(raw_response)

        if not parsed_data:
            _logger.warning("JSOCR: Failed to parse AI response")
            return {
                'success': False,
                'data': None,
                'confidence_data': None,
                'raw_response': raw_response,
                'error': 'Failed to parse AI response as JSON',
                'error_type': 'parse_error',
            }

        confidence_data = self._calculate_confidence(parsed_data)
        metadata = self._build_metadata()

        _logger.info("JSOCR: AI extraction successful")
        return {
            'success': True,
            'data': parsed_data,
            'confidence_data': confidence_data,
            'raw_response': raw_response,
            'error': None,
            'error_type': None,
            'metadata': metadata,
        }

    # ------------------------------------------------------------------
    # Prompt building
    # ------------------------------------------------------------------

    def _build_extraction_prompt(self, text, language='fr'):
        """Build the extraction prompt for the AI provider.

        Args:
            text (str): Invoice text
            language (str): Document language

        Returns:
            str: Complete prompt
        """
        lang_context = {
            'fr': 'francais (Suisse)',
            'de': 'allemand (Suisse)',
            'en': 'anglais',
        }.get(language, 'francais (Suisse)')

        prompt = f"""Tu es un assistant specialise dans l'extraction de donnees de factures.
Analyse le texte de facture suivant et extrait les informations dans un format JSON strict.

CONTEXTE:
- Document en {lang_context}
- Contexte suisse: TVA possible a 7.7%, 2.5%, ou 0%
- Les montants peuvent utiliser la virgule ou le point comme separateur decimal
- L'apostrophe peut etre utilisee comme separateur de milliers (ex: 1'250.00)

TEXTE DE LA FACTURE:
---
{text}
---

INSTRUCTIONS:
1. Extrait UNIQUEMENT les informations presentes dans le document
2. Si une information n'est pas trouvee, utilise null
3. Pour les lignes de facture, extrait autant de lignes que possible
4. Les montants doivent etre des nombres (pas de texte)
5. La date doit etre au format YYYY-MM-DD

REPONDS UNIQUEMENT avec un objet JSON valide (sans texte avant ou apres):
{{
    "supplier_name": "Nom du fournisseur ou null",
    "invoice_date": "YYYY-MM-DD ou null",
    "invoice_number": "Numero de facture ou null",
    "lines": [
        {{
            "description": "Description du produit/service",
            "quantity": 1.0,
            "unit_price": 100.00,
            "amount": 100.00
        }}
    ],
    "amount_untaxed": 100.00,
    "amount_tax": 7.70,
    "amount_total": 107.70,
    "currency": "CHF",
    "payment_reference": "Reference de paiement ou null"
}}"""

        return prompt

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_ai_response(self, response_text):
        """Parse the AI response to extract JSON data.

        Attempts to extract valid JSON from the response, handling cases
        where the model includes extra text before/after the JSON.

        Args:
            response_text (str): Raw response from AI

        Returns:
            dict or None: Parsed data, or None if parsing fails
        """
        if not response_text:
            return None

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        try:
            start = response_text.find('{')
            end = response_text.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_str = response_text[start:end + 1]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        try:
            match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        _logger.warning("JSOCR: Could not parse JSON from AI response")
        return None

    # ------------------------------------------------------------------
    # Confidence calculation
    # ------------------------------------------------------------------

    def _calculate_confidence(self, data):
        """Calculate confidence scores for extracted fields.

        Args:
            data (dict): Extracted invoice data

        Returns:
            dict: Confidence data per field + global score
        """
        confidence = {}

        supplier = data.get('supplier_name')
        if supplier and isinstance(supplier, str) and len(supplier.strip()) > 2:
            confidence['supplier'] = {'value': supplier, 'confidence': 60}
        elif supplier:
            confidence['supplier'] = {'value': supplier, 'confidence': 40}
        else:
            confidence['supplier'] = {'value': None, 'confidence': 0}

        date_val = data.get('invoice_date')
        date_conf = self._validate_date(date_val)
        confidence['date'] = {'value': date_val, 'confidence': date_conf}

        inv_num = data.get('invoice_number')
        if inv_num and isinstance(inv_num, str) and len(inv_num.strip()) > 0:
            confidence['invoice_number'] = {'value': inv_num, 'confidence': 90}
        else:
            confidence['invoice_number'] = {'value': None, 'confidence': 0}

        lines = data.get('lines', [])
        lines_conf = self._calculate_lines_confidence(lines)
        confidence['lines'] = {'value': len(lines), 'confidence': lines_conf}

        amount_untaxed = self._parse_amount(data.get('amount_untaxed'))
        amount_tax = self._parse_amount(data.get('amount_tax'))
        amount_total = self._parse_amount(data.get('amount_total'))

        amounts_conf = self._calculate_amounts_confidence(
            amount_untaxed, amount_tax, amount_total
        )

        confidence['amount_untaxed'] = {
            'value': amount_untaxed,
            'confidence': amounts_conf if amount_untaxed is not None else 0
        }
        confidence['amount_tax'] = {
            'value': amount_tax,
            'confidence': amounts_conf if amount_tax is not None else 0
        }
        confidence['amount_total'] = {
            'value': amount_total,
            'confidence': amounts_conf if amount_total is not None else 0
        }

        weights = {
            'supplier': 15,
            'date': 10,
            'invoice_number': 10,
            'lines': 25,
            'amount_untaxed': 15,
            'amount_tax': 10,
            'amount_total': 15,
        }

        total_weight = sum(weights.values())
        weighted_sum = sum(
            confidence.get(field, {}).get('confidence', 0) * weight
            for field, weight in weights.items()
        )
        global_conf = int(weighted_sum / total_weight) if total_weight > 0 else 0

        confidence['global'] = {'value': global_conf, 'confidence': global_conf}

        return confidence

    def _validate_date(self, date_str):
        """Validate and score a date string.

        Args:
            date_str: Date string or None

        Returns:
            int: Confidence score (0-100)
        """
        if not date_str:
            return 0

        if not isinstance(date_str, str):
            return 0

        try:
            parsed = datetime.strptime(date_str, '%Y-%m-%d')
            today = datetime.now()
            days_diff = abs((today - parsed).days)
            if days_diff < 365:
                return 95
            elif days_diff < 730:
                return 80
            else:
                return 60
        except ValueError:
            pass

        for pattern, format_type in self.DATE_PATTERNS:
            match = re.match(pattern, date_str, re.IGNORECASE)
            if match:
                return 70

        return 30

    def _calculate_lines_confidence(self, lines):
        """Calculate confidence for invoice lines.

        Args:
            lines (list): List of line dictionaries

        Returns:
            int: Confidence score (0-100)
        """
        if not lines or not isinstance(lines, list):
            return 0

        if len(lines) == 0:
            return 0

        valid_lines = 0
        for line in lines:
            if not isinstance(line, dict):
                continue

            has_desc = bool(line.get('description'))
            has_amount = line.get('amount') is not None or (
                line.get('quantity') is not None and line.get('unit_price') is not None
            )

            if has_desc and has_amount:
                valid_lines += 1

        if valid_lines == 0:
            return 20

        ratio = valid_lines / len(lines)
        return int(50 + ratio * 50)

    def _calculate_amounts_confidence(self, untaxed, tax, total):
        """Calculate confidence for amounts based on coherence.

        Checks if HT + TVA ~ TTC (within 1% tolerance).

        Args:
            untaxed: Amount without tax
            tax: Tax amount
            total: Total amount

        Returns:
            int: Confidence score (0-100)
        """
        if total is None:
            return 0

        if untaxed is None and tax is None:
            return 50

        if untaxed is None or tax is None:
            return 60

        calculated_total = untaxed + tax
        if total == 0:
            if calculated_total == 0:
                return 90
            return 30

        diff_percent = abs(calculated_total - total) / abs(total) * 100

        if diff_percent < 0.1:
            return 98
        elif diff_percent < 1:
            return 90
        elif diff_percent < 5:
            _logger.warning(
                "JSOCR: Amount discrepancy >1%%: calculated=%.2f, total=%.2f",
                calculated_total, total
            )
            return 70
        else:
            _logger.warning(
                "JSOCR: Large amount discrepancy: calculated=%.2f, total=%.2f",
                calculated_total, total
            )
            return 40

    def _parse_amount(self, value):
        """Parse an amount value to float.

        Handles various formats:
        - Float/int: returned as-is
        - String: "1'234,56" -> 1234.56

        Args:
            value: Amount value (float, int, str, or None)

        Returns:
            float or None
        """
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            cleaned = value.replace(' ', '').replace("'", '').replace('\xa0', '')
            cleaned = cleaned.replace(',', '.')
            try:
                return float(cleaned)
            except ValueError:
                return None

        return None

    # ------------------------------------------------------------------
    # Supplier matching
    # ------------------------------------------------------------------

    def find_supplier(self, env, supplier_name):
        """Find Odoo partner matching the supplier name.

        Searches in partner name and jsocr_aliases.

        Args:
            env: Odoo environment
            supplier_name (str): Supplier name from AI extraction

        Returns:
            tuple: (res.partner recordset or False, match_type str or None)
                   match_type is 'exact', 'partial', 'alias', or None
        """
        if not supplier_name:
            return False, None

        supplier_name = supplier_name.strip()
        if not supplier_name:
            return False, None

        Partner = env['res.partner']

        partner = Partner.search([
            ('name', '=ilike', supplier_name),
            ('is_company', '=', True),
        ], limit=1)

        if partner:
            _logger.info("JSOCR: Found supplier by exact name match")
            return partner, 'exact'

        partner = Partner.search([
            ('name', 'ilike', supplier_name),
            ('is_company', '=', True),
        ], limit=1)

        if partner:
            _logger.info("JSOCR: Found supplier by partial name match")
            return partner, 'partial'

        partner = Partner.find_by_alias(supplier_name)
        if partner:
            _logger.info("JSOCR: Found supplier by alias match")
            return partner, 'alias'

        _logger.info("JSOCR: No supplier found for extracted name")
        return False, None

    # ------------------------------------------------------------------
    # Date parsing
    # ------------------------------------------------------------------

    def parse_invoice_date(self, date_str):
        """Parse invoice date string to Odoo date format.

        Supports formats: DD.MM.YYYY, DD/MM/YYYY, YYYY-MM-DD

        Args:
            date_str (str): Date string from AI extraction

        Returns:
            str or None: Date in YYYY-MM-DD format, or None
        """
        if not date_str or not isinstance(date_str, str):
            return None

        date_str = date_str.strip()

        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            pass

        for sep in ['.', '/']:
            try:
                parts = date_str.split(sep)
                if len(parts) == 3:
                    day, month, year = parts
                    if len(year) == 2:
                        year = '20' + year
                    parsed = datetime(int(year), int(month), int(day))
                    return parsed.strftime('%Y-%m-%d')
            except (ValueError, IndexError):
                continue

        return None

    # ------------------------------------------------------------------
    # Lines parsing
    # ------------------------------------------------------------------

    def parse_invoice_lines(self, lines_data):
        """Parse and validate invoice lines.

        Args:
            lines_data (list): Lines from AI extraction

        Returns:
            list: Validated lines with proper float values
        """
        if not lines_data or not isinstance(lines_data, list):
            return []

        parsed_lines = []
        for line in lines_data:
            if not isinstance(line, dict):
                continue

            parsed_line = {
                'description': str(line.get('description', '')).strip() or 'Ligne facture',
                'quantity': self._parse_amount(line.get('quantity')) or 1.0,
                'unit_price': self._parse_amount(line.get('unit_price')) or 0.0,
                'amount': self._parse_amount(line.get('amount')) or 0.0,
            }

            if parsed_line['amount'] == 0.0 and parsed_line['unit_price'] > 0:
                parsed_line['amount'] = parsed_line['quantity'] * parsed_line['unit_price']

            parsed_lines.append(parsed_line)

        return parsed_lines
