# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import json
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """Extension of account.move with JSOCR fields for OCR-created invoices.

    This extension adds fields to track the OCR import job, confidence scores,
    and the original PDF source for invoices created via OCR processing.
    """

    _inherit = 'account.move'

    # -------------------------------------------------------------------------
    # JSOCR FIELDS
    # -------------------------------------------------------------------------

    jsocr_import_job_id = fields.Many2one(
        comodel_name='jsocr.import.job',
        string='JSOCR Import Job',
        ondelete='set null',
        index=True,
        help='The OCR import job that created this invoice',
    )

    jsocr_confidence_data = fields.Text(
        string='JSOCR Confidence Data (JSON)',
        help='JSON object containing per-field confidence scores. '
             'Schema: {"field_name": {"value": <any>, "confidence": <int 0-100>}, ...}. '
             'Standard fields: supplier, date, invoice_number, total, subtotal, tax_amount. '
             'Example: {"supplier": {"value": "ACME Corp", "confidence": 95}, '
             '"date": {"value": "2026-01-15", "confidence": 88}}',
    )

    jsocr_source_pdf = fields.Binary(
        string='JSOCR Source PDF',
        attachment=True,
        help='Original PDF file from which this invoice was extracted',
    )

    jsocr_source_pdf_filename = fields.Char(
        string='JSOCR Source PDF Filename',
        help='Filename of the original PDF',
    )

    # -------------------------------------------------------------------------
    # JSOCR CONFIDENCE METHODS
    # -------------------------------------------------------------------------

    def get_field_confidence(self, field_name):
        """Get the confidence score for a specific field.

        Args:
            field_name (str): Name of the field (e.g., 'supplier', 'date', 'total').

        Returns:
            int or None: Confidence score (0-100), or None if not available.
        """
        self.ensure_one()
        if not self.jsocr_confidence_data:
            return None

        if not field_name or not isinstance(field_name, str):
            return None

        try:
            data = json.loads(self.jsocr_confidence_data)
            if not isinstance(data, dict):
                return None
        except (json.JSONDecodeError, TypeError):
            return None

        field_data = data.get(field_name)
        if not isinstance(field_data, dict):
            return None

        confidence = field_data.get('confidence')
        if confidence is None:
            return None

        # Ensure confidence is an integer
        try:
            return int(confidence)
        except (ValueError, TypeError):
            return None

    def get_field_value(self, field_name):
        """Get the extracted value for a specific field.

        Args:
            field_name (str): Name of the field.

        Returns:
            Any or None: The extracted value, or None if not available.
        """
        self.ensure_one()
        if not self.jsocr_confidence_data:
            return None

        if not field_name or not isinstance(field_name, str):
            return None

        try:
            data = json.loads(self.jsocr_confidence_data)
            if not isinstance(data, dict):
                return None
        except (json.JSONDecodeError, TypeError):
            return None

        field_data = data.get(field_name)
        if not isinstance(field_data, dict):
            return None

        return field_data.get('value')

    def get_all_confidences(self):
        """Get all field confidence scores.

        Returns:
            dict: Dictionary mapping field names to confidence scores.
                  Empty dict if no confidence data.
        """
        self.ensure_one()
        if not self.jsocr_confidence_data:
            return {}

        try:
            data = json.loads(self.jsocr_confidence_data)
            if not isinstance(data, dict):
                return {}
        except (json.JSONDecodeError, TypeError):
            return {}

        result = {}
        for field_name, field_data in data.items():
            if isinstance(field_data, dict) and 'confidence' in field_data:
                try:
                    result[field_name] = int(field_data['confidence'])
                except (ValueError, TypeError):
                    pass

        return result

    def set_field_confidence(self, field_name, value, confidence):
        """Set the confidence data for a specific field.

        Stores the value and confidence score in the jsocr_confidence_data JSON
        field. The data is stored in the format:
        {"field_name": {"value": <value>, "confidence": <int>}, ...}

        Standard field names: supplier, date, invoice_number, total, subtotal,
        tax_amount, currency, payment_reference.

        Args:
            field_name (str): Name of the field (e.g., 'supplier', 'date', 'total').
            value: The extracted value (any JSON-serializable type).
            confidence (int): Confidence score (0-100).

        Returns:
            bool: True if set successfully, False otherwise.
        """
        self.ensure_one()
        if not field_name or not isinstance(field_name, str):
            return False

        try:
            confidence = int(confidence)
            if confidence < 0 or confidence > 100:
                _logger.warning(
                    "JSOCR: Invalid confidence value %d for field %s (must be 0-100)",
                    confidence, field_name
                )
                return False
        except (ValueError, TypeError):
            return False

        try:
            data = json.loads(self.jsocr_confidence_data or '{}')
            if not isinstance(data, dict):
                _logger.warning(
                    "JSOCR: Corrupted confidence data on move %s (not a dict), resetting",
                    self.id
                )
                data = {}
        except (json.JSONDecodeError, TypeError) as e:
            _logger.warning(
                "JSOCR: Corrupted JSON in confidence data on move %s: %s, resetting",
                self.id, str(e)
            )
            data = {}

        data[field_name] = {
            'value': value,
            'confidence': confidence,
        }

        self.jsocr_confidence_data = json.dumps(data)
        # Log without field_name to avoid potential sensitive data (NFR8)
        _logger.debug(
            "JSOCR: Set confidence on move %s: %d%%",
            self.id, confidence
        )
        return True

    def get_low_confidence_fields(self, threshold=80):
        """Get fields with confidence below a threshold.

        Args:
            threshold (int): Confidence threshold (default 80).

        Returns:
            list: List of tuples (field_name, confidence) for low-confidence fields.
        """
        self.ensure_one()
        all_confidences = self.get_all_confidences()
        return [
            (field, conf)
            for field, conf in all_confidences.items()
            if conf < threshold
        ]

    # -------------------------------------------------------------------------
    # JSOCR HELPER METHODS
    # -------------------------------------------------------------------------

    def is_jsocr_invoice(self):
        """Check if this invoice was created via JSOCR.

        Returns:
            bool: True if invoice has an associated import job.
        """
        self.ensure_one()
        return bool(self.jsocr_import_job_id)
