# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import json
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class JsocrCorrection(models.Model):
    """User correction for learning and system improvement.

    This model records user corrections made to AI-extracted invoice data.
    Corrections are used to improve future extractions through supplier
    aliases, default charge accounts, and general field value learning.
    """

    _name = 'jsocr.correction'
    _description = 'JSOCR User Correction for Learning'
    _order = 'create_date desc'

    # -------------------------------------------------------------------------
    # FIELDS
    # -------------------------------------------------------------------------

    import_job_id = fields.Many2one(
        comodel_name='jsocr.import.job',
        string='Import Job',
        required=True,
        ondelete='cascade',
        index=True,
        help='The import job this correction is associated with',
    )

    field_name = fields.Char(
        string='Field Name',
        required=True,
        help='Name of the field that was corrected (e.g., supplier, invoice_number)',
    )

    original_value = fields.Char(
        string='Original Value (AI)',
        help='The original value extracted by AI before correction',
    )

    corrected_value = fields.Char(
        string='Corrected Value (User)',
        required=True,
        help='The corrected value provided by the user',
    )

    correction_type = fields.Selection(
        selection=[
            ('supplier_alias', 'Supplier Alias'),
            ('charge_account', 'Charge Account'),
            ('field_value', 'Field Value'),
        ],
        string='Correction Type',
        required=True,
        help='Type of correction: supplier_alias adds a new supplier name alias, '
             'charge_account sets the default charge account for a supplier, '
             'field_value records a generic field correction for learning',
    )

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        readonly=True,
        index=True,
        help='User who made the correction',
    )

    # Note: create_date is automatically provided by Odoo BaseModel
    # (inherited by models.Model) - no need to define it explicitly

    # -------------------------------------------------------------------------
    # ACTION METHODS
    # -------------------------------------------------------------------------

    def apply_correction(self):
        """Apply correction to the system for learning purposes.

        This method applies the correction based on its type:
        - supplier_alias: Adds the original (AI) value as an alias to the
          supplier's jsocr_aliases JSON field in res.partner
        - charge_account: Sets the jsocr_default_account_id on the supplier
          to the corrected value (account ID)
        - field_value: Records the correction for learning but takes no
          immediate action (future enhancement)

        Returns:
            dict: Dictionary mapping correction IDs to their success status.
                  Format: {correction_id: bool, ...}
                  When called on a single record, also accessible as:
                  result[self.id] for the success status.

        Example:
            >>> corrections = self.env['jsocr.correction'].browse([1, 2, 3])
            >>> results = corrections.apply_correction()
            >>> results  # {1: True, 2: False, 3: True}
            >>> all(results.values())  # Check if all succeeded
        """
        results = {}
        for correction in self:
            _logger.debug(
                "JSOCR: Applying correction %s (type=%s) for job %s",
                correction.id, correction.correction_type, correction.import_job_id.id
            )

            if correction.correction_type == 'supplier_alias':
                success = correction._apply_supplier_alias()
            elif correction.correction_type == 'charge_account':
                success = correction._apply_charge_account()
            elif correction.correction_type == 'field_value':
                success = correction._apply_field_value()
            else:
                _logger.warning(
                    "JSOCR: Unknown correction type '%s' for correction %s",
                    correction.correction_type, correction.id
                )
                success = False

            results[correction.id] = success

            if success:
                _logger.info(
                    "JSOCR: Correction %s (type=%s) applied successfully",
                    correction.id, correction.correction_type
                )
            else:
                _logger.warning(
                    "JSOCR: Correction %s (type=%s) could not be applied",
                    correction.id, correction.correction_type
                )

        return results

    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------

    def _apply_supplier_alias(self):
        """Add the original AI value as a supplier alias.

        Adds the original_value to the res.partner.jsocr_aliases JSON array.
        This allows future invoice processing to recognize alternative
        supplier names.

        Note: Requires jsocr_aliases field on res.partner (Story 1.6).
        If the field doesn't exist yet, the method returns False gracefully.

        Returns:
            bool: True if alias was added, False if preconditions not met.
        """
        self.ensure_one()
        if not self.original_value:
            _logger.debug(
                "JSOCR: Cannot add supplier alias - no original_value for correction %s",
                self.id
            )
            return False

        partner = self.import_job_id.invoice_id.partner_id if self.import_job_id.invoice_id else False
        if not partner:
            _logger.debug(
                "JSOCR: Cannot add supplier alias - no partner found for correction %s",
                self.id
            )
            return False

        # Check if jsocr_aliases field exists (added in Story 1.6)
        if 'jsocr_aliases' not in partner._fields:
            _logger.debug(
                "JSOCR: Cannot add supplier alias - jsocr_aliases field not yet available "
                "(requires Story 1.6) for correction %s",
                self.id
            )
            return False

        # Parse existing aliases (default to empty list)
        try:
            aliases = json.loads(partner.jsocr_aliases or '[]')
            if not isinstance(aliases, list):
                aliases = []
        except (json.JSONDecodeError, TypeError):
            aliases = []

        # Add alias if not already present
        if self.original_value not in aliases:
            aliases.append(self.original_value)
            partner.jsocr_aliases = json.dumps(aliases)
            _logger.info(
                "JSOCR: Added supplier alias to partner %s (total aliases: %d)",
                partner.id, len(aliases)
            )

        return True

    def _apply_charge_account(self):
        """Set the default charge account for the supplier.

        Sets the res.partner.jsocr_default_account_id to the account ID
        stored in corrected_value.

        Note: Requires jsocr_default_account_id field on res.partner (Story 1.6).
        If the field doesn't exist yet, the method returns False gracefully.

        Returns:
            bool: True if account was set, False if preconditions not met.
        """
        self.ensure_one()
        partner = self.import_job_id.invoice_id.partner_id if self.import_job_id.invoice_id else False
        if not partner:
            _logger.debug(
                "JSOCR: Cannot set charge account - no partner found for correction %s",
                self.id
            )
            return False

        # Check if jsocr_default_account_id field exists (added in Story 1.6)
        if 'jsocr_default_account_id' not in partner._fields:
            _logger.debug(
                "JSOCR: Cannot set charge account - jsocr_default_account_id field not yet "
                "available (requires Story 1.6) for correction %s",
                self.id
            )
            return False

        try:
            account_id = int(self.corrected_value)
        except (ValueError, TypeError):
            _logger.warning(
                "JSOCR: Invalid account ID in correction %s",
                self.id
            )
            return False

        # Verify account exists
        account = self.env['account.account'].browse(account_id)
        if not account.exists():
            _logger.warning(
                "JSOCR: Account ID %d does not exist (correction %s)",
                account_id, self.id
            )
            return False

        # Validate account is an expense-type account (CR-4)
        valid_account_types = ['expense', 'expense_depreciation', 'expense_direct_cost']
        if account.account_type not in valid_account_types:
            _logger.warning(
                "JSOCR: Account ID %d has invalid type '%s' for expense account "
                "(must be one of %s) in correction %s",
                account_id, account.account_type, valid_account_types, self.id
            )
            return False

        partner.jsocr_default_account_id = account_id
        _logger.info(
            "JSOCR: Set default charge account %d for partner %s",
            account_id, partner.id
        )
        return True

    def _apply_field_value(self):
        """Record field value correction (no immediate action).

        Field value corrections are recorded for future learning but
        do not trigger immediate system changes. They may be used
        later for pattern recognition or machine learning.

        Returns:
            bool: Always True (recording is always successful).
        """
        self.ensure_one()
        # Note: Values are not logged to avoid exposing sensitive data (NFR8)
        _logger.debug(
            "JSOCR: Field value correction %s recorded for field '%s'",
            self.id, self.field_name
        )
        return True
