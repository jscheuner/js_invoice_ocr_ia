# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import logging
import unicodedata
import re
from datetime import datetime

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# French stopwords to remove from descriptions
STOPWORDS = {
    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'a', 'au', 'aux',
    'et', 'ou', 'en', 'pour', 'par', 'sur', 'avec', 'sans', 'dans',
    'ce', 'cette', 'ces', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes',
    'son', 'sa', 'ses', 'notre', 'votre', 'leur', 'leurs',
    'qui', 'que', 'quoi', 'dont', 'ou', 'the', 'a', 'an', 'and', 'or',
    'for', 'to', 'of', 'in', 'on', 'at', 'by', 'from', 'with',
}


class JsocrAccountPattern(models.Model):
    """Learned patterns for account prediction based on invoice line descriptions.

    This model stores associations between supplier, description keywords,
    and expense accounts. Patterns are learned from historical invoices
    and user corrections to improve prediction accuracy over time.
    """

    _name = 'jsocr.account.pattern'
    _description = 'JSOCR Account Pattern - Learned Account Associations'
    _order = 'usage_count desc, last_used desc'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
        required=True,
        ondelete='cascade',
        index=True,
        help='Supplier this pattern applies to',
    )

    keywords = fields.Char(
        string='Keywords',
        required=True,
        index=True,
        help='Normalized keywords from line description',
    )

    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Expense Account',
        required=True,
        ondelete='cascade',
        help='Account to use for lines matching these keywords',
    )

    usage_count = fields.Integer(
        string='Usage Count',
        default=1,
        help='Number of times this pattern has been used or confirmed',
    )

    last_used = fields.Datetime(
        string='Last Used',
        default=fields.Datetime.now,
        help='Last time this pattern was used',
    )

    _sql_constraints = [
        ('unique_partner_keywords',
         'unique(partner_id, keywords)',
         'A pattern with these keywords already exists for this supplier'),
    ]

    # -------------------------------------------------------------------------
    # NORMALIZATION METHODS
    # -------------------------------------------------------------------------

    @staticmethod
    def normalize_text(text):
        """Normalize text for comparison: lowercase, remove accents, remove punctuation.

        Args:
            text (str): Text to normalize

        Returns:
            str: Normalized text with keywords only
        """
        if not text:
            return ''

        # Convert to lowercase
        text = text.lower()

        # Remove accents
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')

        # Remove punctuation and numbers, keep only letters and spaces
        text = re.sub(r'[^a-z\s]', ' ', text)

        # Split into words and remove stopwords
        words = text.split()
        words = [w for w in words if w and w not in STOPWORDS and len(w) > 2]

        # Sort for consistent matching
        words = sorted(set(words))

        return ' '.join(words)

    # -------------------------------------------------------------------------
    # PATTERN MANAGEMENT METHODS
    # -------------------------------------------------------------------------

    @api.model
    def get_or_create_pattern(self, partner_id, description, account_id):
        """Get existing pattern or create new one.

        Args:
            partner_id (int): Supplier partner ID
            description (str): Line description
            account_id (int): Account to associate

        Returns:
            jsocr.account.pattern: The pattern record
        """
        keywords = self.normalize_text(description)
        if not keywords:
            return self.browse()

        # Search for existing pattern
        pattern = self.search([
            ('partner_id', '=', partner_id),
            ('keywords', '=', keywords),
        ], limit=1)

        if pattern:
            # Update existing pattern
            pattern.write({
                'account_id': account_id,
                'usage_count': pattern.usage_count + 1,
                'last_used': fields.Datetime.now(),
            })
            _logger.info(
                "JSOCR: Updated pattern for partner %s, keywords '%s', count=%d",
                partner_id, keywords[:30], pattern.usage_count
            )
        else:
            # Create new pattern
            pattern = self.create({
                'partner_id': partner_id,
                'keywords': keywords,
                'account_id': account_id,
                'usage_count': 1,
                'last_used': fields.Datetime.now(),
            })
            _logger.info(
                "JSOCR: Created pattern for partner %s, keywords '%s'",
                partner_id, keywords[:30]
            )

        return pattern

    @api.model
    def find_matching_pattern(self, partner_id, description):
        """Find best matching pattern for a description.

        Args:
            partner_id (int): Supplier partner ID
            description (str): Line description to match

        Returns:
            tuple: (account_id, confidence, source) or (None, 0, None)
        """
        keywords = self.normalize_text(description)
        if not keywords:
            return None, 0, None

        # First try exact match
        pattern = self.search([
            ('partner_id', '=', partner_id),
            ('keywords', '=', keywords),
        ], limit=1)

        if pattern:
            # Confidence based on usage count
            confidence = min(70 + pattern.usage_count * 10, 100)
            _logger.info(
                "JSOCR: Exact pattern match for '%s', account=%s, confidence=%d",
                keywords[:30], pattern.account_id.code, confidence
            )
            return pattern.account_id.id, confidence, 'pattern'

        # Try partial match - find patterns where keywords overlap
        search_words = set(keywords.split())
        if not search_words:
            return None, 0, None

        patterns = self.search([
            ('partner_id', '=', partner_id),
        ], order='usage_count desc', limit=20)

        best_match = None
        best_score = 0

        for pattern in patterns:
            pattern_words = set(pattern.keywords.split())
            if not pattern_words:
                continue

            # Calculate Jaccard similarity
            intersection = len(search_words & pattern_words)
            union = len(search_words | pattern_words)

            if union > 0:
                similarity = intersection / union
                # Weight by usage count
                score = similarity * (1 + min(pattern.usage_count, 10) * 0.05)

                if score > best_score and similarity > 0.3:
                    best_score = score
                    best_match = pattern

        if best_match:
            confidence = int(min(best_score * 80, 85))
            _logger.info(
                "JSOCR: Partial pattern match for '%s', account=%s, confidence=%d",
                keywords[:30], best_match.account_id.code, confidence
            )
            return best_match.account_id.id, confidence, 'pattern'

        return None, 0, None

    def increment_usage(self):
        """Increment usage count for this pattern."""
        self.ensure_one()
        self.write({
            'usage_count': self.usage_count + 1,
            'last_used': fields.Datetime.now(),
        })
