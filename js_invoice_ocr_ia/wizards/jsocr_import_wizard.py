# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class JsocrImportWizard(models.TransientModel):
    """Manual multi-PDF import wizard.

    Lets users upload invoice PDFs directly from Odoo instead of dropping
    them in the watch folder, and triggers processing immediately instead
    of waiting for the next cron run.
    """

    _name = 'jsocr.import.wizard'
    _description = 'JSOCR Import PDF Wizard'

    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string='Fichiers PDF',
        required=True,
        help='Fichiers PDF de factures fournisseurs a importer',
    )

    process_immediately = fields.Boolean(
        string='Traiter immediatement',
        default=True,
        help='Lance le traitement (OCR + IA + creation facture) sans attendre le cron',
    )

    def action_import(self):
        """Create an import job per uploaded PDF and optionally process now.

        Returns:
            dict: Action opening the created jobs
        """
        self.ensure_one()

        if not self.attachment_ids:
            raise UserError("Veuillez selectionner au moins un fichier PDF.")

        # sudo: standard OCR users may upload invoices even without
        # create rights on jsocr.import.job (create_uid stays the uploader)
        Job = self.env['jsocr.import.job'].sudo()
        jobs = Job.browse()
        skipped = []

        for attachment in self.attachment_ids:
            name = attachment.name or 'sans_nom'
            is_pdf = (
                attachment.mimetype == 'application/pdf'
                or name.lower().endswith('.pdf')
            )
            if not is_pdf or not attachment.datas:
                skipped.append(name)
                continue

            job = Job.create({
                'pdf_file': attachment.datas,
                'pdf_filename': name,
            })
            job.action_submit()
            jobs |= job
            _logger.info("JSOCR: Wizard created job %s for upload %s", job.id, name)

        if skipped:
            _logger.warning(
                "JSOCR: Wizard skipped %d non-PDF file(s): %s",
                len(skipped), ', '.join(skipped)
            )

        if not jobs:
            raise UserError(
                "Aucun fichier PDF valide. Fichiers ignores: " + ', '.join(skipped)
            )

        if self.process_immediately:
            cron = self.env.ref(
                'js_invoice_ocr_ia.ir_cron_jsocr_process_jobs',
                raise_if_not_found=False,
            )
            if cron:
                cron.sudo()._trigger()
                _logger.info("JSOCR: Wizard triggered immediate job processing")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Jobs importes',
            'res_model': 'jsocr.import.job',
            'view_mode': 'list,kanban,form',
            'domain': [('id', 'in', jobs.ids)],
            'target': 'current',
        }
