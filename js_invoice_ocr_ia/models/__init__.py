# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

# Models will be imported here as they are created
# Python filename (snake_case) → Odoo model name (dot notation)
from . import jsocr_config        # defines model: jsocr.config
from . import jsocr_import_job    # defines model: jsocr.import.job
from . import jsocr_mask          # defines model: jsocr.mask
from . import jsocr_correction    # defines model: jsocr.correction
from . import res_partner         # extends model: res.partner
from . import account_move        # extends model: account.move
