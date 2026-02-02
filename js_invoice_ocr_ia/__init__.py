# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

from . import models
from . import services
from . import wizards


def post_init_hook(cr, registry):
    """Check if required OCA module queue_job is installed."""
    import logging
    _logger = logging.getLogger(__name__)

    cr.execute("SELECT state FROM ir_module_module WHERE name='queue_job'")
    result = cr.fetchone()

    if not result or result[0] != 'installed':
        _logger.warning(
            "JSOCR: Module 'queue_job' (OCA) is required but not installed. "
            "Please install queue_job from https://github.com/OCA/queue before using this addon. "
            "The addon will not function correctly without queue_job."
        )
    else:
        _logger.info("JSOCR: Required dependency 'queue_job' is installed.")
