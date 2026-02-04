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

    # -------------------------------------------------------------------------
    # LEARNING HOOK (Story 4.20)
    # -------------------------------------------------------------------------

    def action_post(self):
        """Override action_post to learn from account corrections on OCR invoices.

        When an OCR-created invoice is validated, compare predicted accounts
        with final accounts on each line. If they differ, create a correction
        record and update the account pattern for future predictions.
        """
        res = super().action_post()

        for move in self:
            if not move.jsocr_import_job_id or not move.partner_id:
                continue
            try:
                move._learn_account_corrections()
            except Exception as e:
                _logger.error(
                    "JSOCR: Failed to learn account corrections for move %s: %s",
                    move.id, type(e).__name__
                )

        return res

    def _learn_account_corrections(self):
        """Detect and learn from account corrections on invoice lines (Story 4.20).

        For each line where the final account differs from the predicted account,
        creates a jsocr.correction record and updates the jsocr.account.pattern.
        """
        self.ensure_one()

        if not self.jsocr_import_job_id or not self.partner_id:
            return

        PatternModel = self.env['jsocr.account.pattern']
        CorrectionModel = self.env['jsocr.correction']

        for line in self.invoice_line_ids:
            if not line.name or not line.account_id:
                continue
            # Skip non-expense accounts
            if line.account_id.account_type not in (
                'expense', 'expense_depreciation', 'expense_direct_cost'
            ):
                continue

            # Always update/create pattern for confirmed lines
            PatternModel.get_or_create_pattern(
                self.partner_id.id,
                line.name,
                line.account_id.id,
            )

            # If account was changed from prediction, record correction
            if line.jsocr_predicted_account_id and line.jsocr_predicted_account_id != line.account_id:
                CorrectionModel.create({
                    'import_job_id': self.jsocr_import_job_id.id,
                    'field_name': 'account_id',
                    'original_value': line.jsocr_predicted_account_id.code,
                    'corrected_value': line.account_id.code,
                    'correction_type': 'line_account',
                })
                _logger.info(
                    "JSOCR: Learned account correction on move %s: %s -> %s",
                    self.id,
                    line.jsocr_predicted_account_id.code,
                    line.account_id.code,
                )


class AccountMoveLine(models.Model):
    """Extension of account.move.line with JSOCR prediction fields.

    Adds fields to track the predicted account, confidence score,
    and prediction source for lines created via OCR processing.
    """

    _inherit = 'account.move.line'

    jsocr_account_confidence = fields.Integer(
        string='Account Confidence',
        help='Confidence score for predicted account (0-100). '
             'Green >= 80, Orange 50-79, Red < 50',
    )

    jsocr_account_source = fields.Selection(
        selection=[
            ('pattern', 'Learned Pattern'),
            ('history', 'Historical Analysis'),
            ('default', 'Default Account'),
        ],
        string='Prediction Source',
        help='How the account was predicted: '
             'pattern = from learned patterns, '
             'history = from similar historical lines, '
             'default = fallback expense account',
    )

    jsocr_predicted_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Predicted Account',
        ondelete='set null',
        help='The account originally predicted by OCR. '
             'Used to detect user corrections for learning.',
    )
