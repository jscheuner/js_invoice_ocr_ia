# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import json
import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Extension of res.partner with JSOCR fields for supplier OCR matching.

    This extension adds fields to track supplier name aliases and default
    expense accounts for automated invoice processing.
    """

    _inherit = 'res.partner'

    # -------------------------------------------------------------------------
    # JSOCR FIELDS
    # -------------------------------------------------------------------------

    jsocr_aliases = fields.Text(
        string='JSOCR Aliases (JSON)',
        help='JSON array of supplier name aliases for OCR matching. '
             'Format: ["Alias 1", "Alias 2", ...]',
    )

    jsocr_default_account_id = fields.Many2one(
        comodel_name='account.account',
        string='JSOCR Default Expense Account',
        help='Default expense account to use when creating invoices for this supplier',
    )

    jsocr_mask_ids = fields.One2many(
        comodel_name='jsocr.mask',
        inverse_name='partner_id',
        string='JSOCR Extraction Masks',
        help='Extraction masks associated with this supplier',
    )

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------

    @api.constrains('jsocr_aliases')
    def _check_jsocr_aliases_format(self):
        """Validate jsocr_aliases is a valid JSON array of strings.

        Raises:
            ValidationError: If jsocr_aliases is not valid JSON or not an array.
        """
        for partner in self:
            if partner.jsocr_aliases:
                try:
                    aliases = json.loads(partner.jsocr_aliases)
                    if not isinstance(aliases, list):
                        raise ValidationError(
                            f"JSOCR Aliases for partner '{partner.name}' must be a JSON array, "
                            f"got {type(aliases).__name__}"
                        )
                    for alias in aliases:
                        if not isinstance(alias, str):
                            raise ValidationError(
                                f"JSOCR Aliases for partner '{partner.name}' must contain only strings"
                            )
                except json.JSONDecodeError as e:
                    raise ValidationError(
                        f"JSOCR Aliases for partner '{partner.name}' contains invalid JSON: {e}"
                    )

    # -------------------------------------------------------------------------
    # JSOCR ALIAS METHODS
    # -------------------------------------------------------------------------

    def add_alias(self, alias_name):
        """Add an alias to the supplier's alias list.

        Adds the given name to the jsocr_aliases JSON array if not already present.
        Creates a new array if none exists.

        Args:
            alias_name (str): The alias name to add.

        Returns:
            bool: True if alias was added, False if already present or invalid.
        """
        self.ensure_one()
        if not alias_name or not isinstance(alias_name, str):
            _logger.debug(
                "JSOCR: Cannot add alias - invalid alias_name for partner %s",
                self.id
            )
            return False

        alias_name = alias_name.strip()
        if not alias_name:
            return False

        try:
            aliases = json.loads(self.jsocr_aliases or '[]')
            if not isinstance(aliases, list):
                aliases = []
        except (json.JSONDecodeError, TypeError):
            aliases = []

        if alias_name in aliases:
            _logger.debug(
                "JSOCR: Alias already exists for partner %s",
                self.id
            )
            return False

        aliases.append(alias_name)
        self.jsocr_aliases = json.dumps(aliases)
        _logger.info(
            "JSOCR: Added alias to partner %s (total aliases: %d)",
            self.id, len(aliases)
        )
        return True

    def has_alias(self, alias_name):
        """Check if an alias exists for this supplier.

        Args:
            alias_name (str): The alias name to check.

        Returns:
            bool: True if the alias exists, False otherwise.
        """
        self.ensure_one()
        if not alias_name or not isinstance(alias_name, str):
            return False

        alias_name = alias_name.strip()
        if not alias_name:
            return False

        try:
            aliases = json.loads(self.jsocr_aliases or '[]')
            if not isinstance(aliases, list):
                return False
        except (json.JSONDecodeError, TypeError):
            return False

        return alias_name in aliases

    def get_aliases(self):
        """Get all aliases for this supplier.

        Returns:
            list: List of alias strings, empty list if none.
        """
        self.ensure_one()
        try:
            aliases = json.loads(self.jsocr_aliases or '[]')
            if not isinstance(aliases, list):
                return []
            return aliases
        except (json.JSONDecodeError, TypeError):
            return []

    def remove_alias(self, alias_name):
        """Remove an alias from the supplier's alias list.

        Args:
            alias_name (str): The alias name to remove.

        Returns:
            bool: True if alias was removed, False if not found.
        """
        self.ensure_one()
        if not alias_name or not isinstance(alias_name, str):
            return False

        alias_name = alias_name.strip()
        if not alias_name:
            return False

        try:
            aliases = json.loads(self.jsocr_aliases or '[]')
            if not isinstance(aliases, list):
                return False
        except (json.JSONDecodeError, TypeError):
            return False

        if alias_name not in aliases:
            return False

        aliases.remove(alias_name)
        self.jsocr_aliases = json.dumps(aliases)
        _logger.info(
            "JSOCR: Removed alias from partner %s (remaining aliases: %d)",
            self.id, len(aliases)
        )
        return True

    # -------------------------------------------------------------------------
    # JSOCR SEARCH METHODS
    # -------------------------------------------------------------------------

    @api.model
    def find_by_alias(self, alias_name):
        """Find a partner by alias name.

        Uses optimized SQL LIKE search on the JSON field for performance (NFR2).
        The search is case-sensitive and matches exact alias strings within the
        JSON array.

        Args:
            alias_name (str): The alias name to search for.

        Returns:
            res.partner or False: The matching partner record, or False if not found.
        """
        if not alias_name or not isinstance(alias_name, str):
            return False

        alias_name = alias_name.strip()
        if not alias_name:
            return False

        # Optimized search using SQL LIKE on the JSON field (PROB-2 fix)
        # Search for the alias as a JSON string element: "alias_name"
        # This avoids loading all partners into memory
        search_pattern = f'"{alias_name}"'
        candidates = self.search([
            ('jsocr_aliases', 'ilike', search_pattern),
        ], limit=100)  # Reasonable limit for performance

        # Verify exact match (LIKE may have false positives)
        for partner in candidates:
            if partner.has_alias(alias_name):
                _logger.debug(
                    "JSOCR: Found partner %s by alias",
                    partner.id
                )
                return partner

        _logger.debug("JSOCR: No partner found for alias")
        return False
