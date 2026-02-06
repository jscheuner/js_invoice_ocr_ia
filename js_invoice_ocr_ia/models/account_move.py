# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import json
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """Extension of account.move with JSOCR fields for OCR-created invoices.

    This extension adds fields to track the OCR import job and confidence scores
    for invoices created via OCR processing.
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

    jsocr_amount_alert = fields.Boolean(
        string='High Amount Alert',
        compute='_compute_jsocr_amount_alert',
        help='True if invoice total exceeds the configured alert threshold',
    )

    jsocr_amount_mismatch = fields.Boolean(
        string='Amount Mismatch',
        default=False,
        help='True if extracted total differs from computed total by more than 0.03, '
             'or if HT/TTC detection was inconclusive',
    )

    jsocr_global_confidence = fields.Integer(
        string='Global Confidence',
        compute='_compute_jsocr_global_confidence',
        help='Average confidence score across all extracted fields (0-100)',
    )

    # Per-field confidence detail fields (computed from JSON)
    jsocr_conf_supplier = fields.Integer(
        compute='_compute_jsocr_conf_details', string='Fournisseur',
    )
    jsocr_conf_date = fields.Integer(
        compute='_compute_jsocr_conf_details', string='Date',
    )
    jsocr_conf_invoice_number = fields.Integer(
        compute='_compute_jsocr_conf_details', string='N° facture',
    )
    jsocr_conf_lines = fields.Integer(
        compute='_compute_jsocr_conf_details', string='Lignes',
    )
    jsocr_conf_amount_untaxed = fields.Integer(
        compute='_compute_jsocr_conf_details', string='Montant HT',
    )
    jsocr_conf_amount_tax = fields.Integer(
        compute='_compute_jsocr_conf_details', string='TVA',
    )
    jsocr_conf_amount_total = fields.Integer(
        compute='_compute_jsocr_conf_details', string='Total',
    )

    # Badge fields for inline display (Char "XX%" with colored badge widget)
    jsocr_conf_supplier_badge = fields.Char(
        compute='_compute_jsocr_conf_badges', string='Fournisseur',
    )
    jsocr_conf_date_badge = fields.Char(
        compute='_compute_jsocr_conf_badges', string='Date',
    )
    jsocr_conf_invoice_number_badge = fields.Char(
        compute='_compute_jsocr_conf_badges', string='N° facture',
    )

    # -------------------------------------------------------------------------
    # JSOCR COMPUTED FIELDS FOR UI (Story 5.2, 5.3)
    # -------------------------------------------------------------------------

    @api.depends('amount_total')
    def _compute_jsocr_amount_alert(self):
        """Check if invoice total exceeds the configured alert threshold."""
        config = self.env['jsocr.config'].search([], limit=1)
        threshold = config.alert_amount_threshold if config else 0
        for move in self:
            if not move.jsocr_import_job_id or not threshold:
                move.jsocr_amount_alert = False
            else:
                move.jsocr_amount_alert = move.amount_total > threshold

    @api.depends('jsocr_confidence_data')
    def _compute_jsocr_global_confidence(self):
        """Compute average confidence from all fields."""
        for move in self:
            confidences = move.get_all_confidences()
            if confidences:
                move.jsocr_global_confidence = int(
                    sum(confidences.values()) / len(confidences)
                )
            else:
                move.jsocr_global_confidence = 0

    @api.depends('jsocr_confidence_data')
    def _compute_jsocr_conf_details(self):
        """Compute individual confidence fields from JSON data."""
        field_map = {
            'supplier': 'jsocr_conf_supplier',
            'date': 'jsocr_conf_date',
            'invoice_number': 'jsocr_conf_invoice_number',
            'lines': 'jsocr_conf_lines',
            'amount_untaxed': 'jsocr_conf_amount_untaxed',
            'amount_tax': 'jsocr_conf_amount_tax',
            'amount_total': 'jsocr_conf_amount_total',
        }
        for move in self:
            data = {}
            if move.jsocr_confidence_data:
                try:
                    data = json.loads(move.jsocr_confidence_data)
                    if not isinstance(data, dict):
                        data = {}
                except (json.JSONDecodeError, TypeError):
                    data = {}
            for json_key, field_name in field_map.items():
                conf = 0
                entry = data.get(json_key)
                if isinstance(entry, dict):
                    try:
                        conf = int(entry.get('confidence', 0))
                    except (ValueError, TypeError):
                        conf = 0
                setattr(move, field_name, conf)

    @api.depends('jsocr_confidence_data')
    def _compute_jsocr_conf_badges(self):
        """Compute badge strings ('XX%') for inline confidence display."""
        for move in self:
            move.jsocr_conf_supplier_badge = (
                f"{move.jsocr_conf_supplier}%" if move.jsocr_conf_supplier else ''
            )
            move.jsocr_conf_date_badge = (
                f"{move.jsocr_conf_date}%" if move.jsocr_conf_date else ''
            )
            move.jsocr_conf_invoice_number_badge = (
                f"{move.jsocr_conf_invoice_number}%" if move.jsocr_conf_invoice_number else ''
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

    def action_revalidate_jsocr_total(self):
        """Revalidate invoice total against extracted total.

        Button action to clear the mismatch flag if the user has manually
        corrected the invoice lines and the total now matches.

        Returns:
            dict: Notification action with result message
        """
        self.ensure_one()

        if not self.jsocr_import_job_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Non applicable',
                    'message': 'Cette facture n\'est pas issue de l\'OCR.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        job = self.jsocr_import_job_id
        extracted_total = job.extracted_amount_total

        if not extracted_total:
            self.jsocr_amount_mismatch = False
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Validation OK',
                    'message': 'Pas de total extrait a comparer. Flag efface.',
                    'type': 'success',
                    'sticky': False,
                }
            }

        ecart = abs(self.amount_total - extracted_total)
        tolerance = 0.03

        if ecart <= tolerance:
            self.jsocr_amount_mismatch = False
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Validation OK',
                    'message': f'Total correct (ecart: {ecart:.2f} CHF). Flag efface.',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            self.jsocr_amount_mismatch = True
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Ecart detecte',
                    'message': f'Ecart de {ecart:.2f} CHF entre total calcule ({self.amount_total:.2f}) '
                               f'et total extrait ({extracted_total:.2f}).',
                    'type': 'warning',
                    'sticky': True,
                }
            }

    # -------------------------------------------------------------------------
    # LEARNING HOOK (Story 4.20)
    # -------------------------------------------------------------------------

    def action_post(self):
        """Override action_post to learn from corrections on OCR invoices.

        When an OCR-created invoice is validated:
        - Story 6.1: Detect supplier corrections and add aliases
        - Story 6.2: Detect charge account corrections
        - Story 4.20: Detect line account corrections and update patterns
        - Story 6.7: Trigger mask generation if enough invoices
        """
        res = super().action_post()

        for move in self:
            if not move.jsocr_import_job_id:
                continue
            try:
                move._learn_supplier_correction()
                move._learn_charge_account_correction()
                if move.partner_id:
                    move._learn_account_corrections()
                    move._trigger_mask_generation()
            except Exception as e:
                _logger.error(
                    "JSOCR: Failed to learn corrections for move %s: %s",
                    move.id, type(e).__name__
                )

        return res

    def _learn_supplier_correction(self):
        """Detect and learn from supplier corrections (Story 6.1 - FR25, FR31).

        If the user changed the supplier from what the AI detected,
        add the AI-detected name as an alias for the correct supplier.
        """
        self.ensure_one()
        job = self.jsocr_import_job_id
        if not job or not self.partner_id:
            return

        extracted_name = job.extracted_supplier_name
        if not extracted_name:
            return

        # Check if the supplier was changed (AI detected a different one or none)
        ai_partner = job.partner_id
        if ai_partner and ai_partner.id == self.partner_id.id:
            return  # No change

        # The user corrected the supplier - add the AI name as alias
        CorrectionModel = self.env['jsocr.correction']
        self.partner_id.add_alias(extracted_name)

        CorrectionModel.create({
            'import_job_id': job.id,
            'field_name': 'partner_id',
            'original_value': extracted_name,
            'corrected_value': self.partner_id.name,
            'correction_type': 'supplier_alias',
        })
        _logger.info(
            "JSOCR: Learned supplier alias '%s' for partner %s",
            extracted_name[:30], self.partner_id.id
        )

    def _learn_charge_account_correction(self):
        """Detect and learn default charge account for supplier (Story 6.2 - FR26).

        When a supplier invoice is validated, check the most used account
        across lines and set it as the supplier's default if not already set.
        """
        self.ensure_one()
        if not self.partner_id or not self.jsocr_import_job_id:
            return

        # Count accounts used on expense lines
        account_counts = {}
        for line in self.invoice_line_ids:
            if not line.account_id:
                continue
            if line.account_id.account_type not in (
                'expense', 'expense_depreciation', 'expense_direct_cost'
            ):
                continue
            aid = line.account_id.id
            account_counts[aid] = account_counts.get(aid, 0) + 1

        if not account_counts:
            return

        # Find the most used account
        most_used_account_id = max(account_counts, key=account_counts.get)

        # Update supplier default if different
        current_default = self.partner_id.jsocr_default_account_id.id if self.partner_id.jsocr_default_account_id else None
        if current_default != most_used_account_id:
            old_code = self.partner_id.jsocr_default_account_id.code if self.partner_id.jsocr_default_account_id else 'none'
            new_account = self.env['account.account'].browse(most_used_account_id)
            self.partner_id.jsocr_default_account_id = most_used_account_id

            self.env['jsocr.correction'].create({
                'import_job_id': self.jsocr_import_job_id.id,
                'field_name': 'default_account_id',
                'original_value': old_code,
                'corrected_value': new_account.code,
                'correction_type': 'charge_account',
            })
            _logger.info(
                "JSOCR: Updated default account for partner %s to %s",
                self.partner_id.id, new_account.code
            )

    def _trigger_mask_generation(self):
        """Trigger automatic mask generation if enough invoices (Story 6.7).

        After 3+ successful invoices from the same supplier, generate a mask
        capturing the common extraction patterns.
        """
        self.ensure_one()
        if not self.partner_id:
            return

        MaskModel = self.env['jsocr.mask']

        # Check if mask already exists for this supplier
        existing_mask = MaskModel.search([
            ('partner_id', '=', self.partner_id.id),
            ('active', '=', True),
        ], limit=1)

        if existing_mask:
            # Increment usage count on existing mask
            existing_mask.action_increment_usage()
            return

        # Count successful invoices for this supplier
        done_count = self.search_count([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted'),
            ('jsocr_import_job_id', '!=', False),
        ])

        if done_count >= 3:
            MaskModel.generate_mask_from_history(self.partner_id.id)

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

    jsocr_confidence_badge = fields.Char(
        string='Confidence',
        compute='_compute_jsocr_confidence_badge',
        help='Visual confidence indicator for the predicted account',
    )

    @api.depends('jsocr_account_confidence')
    def _compute_jsocr_confidence_badge(self):
        """Compute a display string for the confidence badge."""
        for line in self:
            conf = line.jsocr_account_confidence
            if not conf:
                line.jsocr_confidence_badge = ''
            elif conf >= 80:
                line.jsocr_confidence_badge = f'{conf}%'
            elif conf >= 50:
                line.jsocr_confidence_badge = f'{conf}%'
            else:
                line.jsocr_confidence_badge = f'{conf}%'
