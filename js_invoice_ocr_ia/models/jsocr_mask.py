# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import json
import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class JsocrMask(models.Model):
    """Extraction mask per supplier for customized invoice data extraction.

    This model stores JSON-based extraction masks that define how to extract
    invoice data for specific suppliers. Each mask can define field patterns,
    zones, and expected values for a supplier's invoice format.
    """

    _name = 'jsocr.mask'
    _description = 'JSOCR Extraction Mask per Supplier'
    _order = 'usage_count desc, name'

    # -------------------------------------------------------------------------
    # FIELDS
    # -------------------------------------------------------------------------

    name = fields.Char(
        string='Mask Name',
        required=True,
        help='Descriptive name for this extraction mask',
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
        ondelete='cascade',
        index=True,
        help='Supplier this mask applies to',
    )

    mask_data = fields.Text(
        string='Mask Data (JSON)',
        default='{}',
        help='JSON structure defining extraction zones and patterns',
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='If unchecked, the mask is archived and hidden from default searches',
    )

    usage_count = fields.Integer(
        string='Usage Count',
        default=0,
        readonly=True,
        help='Number of times this mask was used successfully for extraction',
    )

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------

    @api.constrains('mask_data')
    def _validate_mask_data(self):
        """Validate that mask_data contains valid JSON and check expected structure.

        The expected structure includes 'version' and 'fields' keys. If these
        are missing, a warning is logged but validation still passes to allow
        flexibility for future mask format evolution.

        Raises:
            ValidationError: If mask_data is not valid JSON.
        """
        for mask in self:
            if mask.mask_data:
                try:
                    data = json.loads(mask.mask_data)
                except json.JSONDecodeError as e:
                    raise ValidationError(
                        f"Invalid JSON in mask_data for mask '{mask.name}': {e}"
                    )
                # Check expected structure and warn if missing
                if isinstance(data, dict) and data:
                    if 'version' not in data:
                        _logger.warning(
                            "JSOCR: Mask %s (%s) missing 'version' key in mask_data",
                            mask.id, mask.name
                        )
                    if 'fields' not in data:
                        _logger.warning(
                            "JSOCR: Mask %s (%s) missing 'fields' key in mask_data",
                            mask.id, mask.name
                        )

    # -------------------------------------------------------------------------
    # ACTION METHODS
    # -------------------------------------------------------------------------

    def action_increment_usage(self):
        """Increment usage counter when mask is used successfully.

        Called by the processing service when a mask is successfully used
        to extract invoice data. This helps identify popular/effective masks.
        """
        for mask in self:
            mask.usage_count += 1
            _logger.debug(
                "JSOCR: Mask %s (%s) usage incremented to %d",
                mask.id, mask.name, mask.usage_count
            )

    # -------------------------------------------------------------------------
    # PUBLIC API METHODS
    # -------------------------------------------------------------------------

    @api.model
    def get_mask_for_partner(self, partner_id):
        """Get the most used active mask for a given partner.

        This method retrieves the best mask to use for extracting invoice
        data from a specific supplier. The mask with the highest usage_count
        is returned (model is ordered by usage_count desc).

        Args:
            partner_id (int): The res.partner ID to search masks for.
                             Returns False immediately if None, 0, or falsy.

        Returns:
            jsocr.mask or False: The most used active mask for the partner,
                                or False if partner_id is invalid or no
                                active mask exists for the partner.
        """
        if not partner_id:
            _logger.debug(
                "JSOCR: get_mask_for_partner called with invalid partner_id: %s",
                partner_id
            )
            return False
        # Model is ordered by usage_count desc, so first result is most used
        mask = self.search([
            ('partner_id', '=', partner_id),
            ('active', '=', True),
        ], limit=1)
        if mask:
            _logger.debug(
                "JSOCR: Found mask %s (usage_count=%d) for partner %s",
                mask.id, mask.usage_count, partner_id
            )
        else:
            _logger.debug(
                "JSOCR: No active mask found for partner %s",
                partner_id
            )
        return mask or False
