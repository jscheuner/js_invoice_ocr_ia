# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import base64
import json
import logging
from datetime import datetime
from pathlib import Path

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Retry configuration from architecture.md
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]  # seconds - backoff delays for retry scheduling


class JsocrImportJob(models.Model):
    """Import job for PDF invoice processing with state machine.

    This model tracks the lifecycle of PDF invoice imports through OCR and AI
    analysis. It implements a strict state machine with retry capabilities.

    Inherits mail.thread for activity tracking and chatter integration.
    """

    _name = 'jsocr.import.job'
    _description = 'JSOCR Import Job - PDF Invoice Processing'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # -------------------------------------------------------------------------
    # FIELDS
    # -------------------------------------------------------------------------

    name = fields.Char(
        string='Job Name',
        compute='_compute_name',
        store=True,
        help='Auto-generated job name: Job #ID - filename',
    )

    pdf_file = fields.Binary(
        string='PDF File',
        required=True,
        attachment=True,
        help='The PDF file to process',
    )

    pdf_filename = fields.Char(
        string='Filename',
        required=True,
        help='Original filename of the PDF',
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('done', 'Done'),
            ('error', 'Error'),
            ('failed', 'Failed'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        help='Current state of the import job',
    )

    # Extraction results
    extracted_text = fields.Text(
        string='Extracted Text',
        copy=False,
        help='Raw text extracted from PDF via OCR',
    )

    ai_response = fields.Text(
        string='AI Response (JSON)',
        copy=False,
        help='Raw JSON response from Ollama AI analysis',
    )

    confidence_data = fields.Text(
        string='Confidence Data (JSON)',
        copy=False,
        help='Per-field confidence scores in JSON format',
    )

    error_message = fields.Text(
        string='Error Message',
        copy=False,
        help='Error details if job failed',
    )

    detected_language = fields.Selection(
        selection=[
            ('fr', 'French'),
            ('de', 'German'),
            ('en', 'English'),
        ],
        string='Detected Language',
        default='fr',
        help='Language detected in the PDF document (ISO 639-1 code)',
    )

    # Relations
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Generated Invoice',
        ondelete='set null',
        copy=False,
        help='Link to the generated supplier invoice',
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Detected Supplier',
        ondelete='set null',
        copy=False,
        help='Supplier detected from AI extraction',
    )

    correction_ids = fields.One2many(
        comodel_name='jsocr.correction',
        inverse_name='import_job_id',
        string='Corrections',
        copy=False,
        help='User corrections associated with this import job',
    )

    # Extracted data fields (Story 4.3-4.6)
    extracted_supplier_name = fields.Char(
        string='Extracted Supplier',
        copy=False,
        help='Supplier name extracted by AI',
    )

    extracted_invoice_date = fields.Date(
        string='Extracted Date',
        copy=False,
        help='Invoice date extracted by AI',
    )

    extracted_invoice_number = fields.Char(
        string='Extracted Invoice Number',
        copy=False,
        help='Invoice number (supplier reference) extracted by AI',
    )

    extracted_lines = fields.Text(
        string='Extracted Lines (JSON)',
        copy=False,
        help='Invoice lines extracted by AI in JSON format',
    )

    extracted_amount_untaxed = fields.Float(
        string='Extracted Amount Untaxed',
        digits='Account',
        copy=False,
        help='Amount without tax extracted by AI',
    )

    extracted_amount_tax = fields.Float(
        string='Extracted Tax Amount',
        digits='Account',
        copy=False,
        help='Tax amount extracted by AI',
    )

    extracted_amount_total = fields.Float(
        string='Extracted Total',
        digits='Account',
        copy=False,
        help='Total amount extracted by AI',
    )

    # Retry management
    retry_count = fields.Integer(
        string='Retry Count',
        default=0,
        copy=False,
        help='Number of retry attempts (max 3)',
    )

    next_retry_delay = fields.Integer(
        string='Next Retry Delay',
        compute='_compute_next_retry_delay',
        help='Delay in seconds before next retry (backoff: 5s, 15s, 30s)',
    )

    # Computed fields
    can_retry = fields.Boolean(
        string='Can Retry',
        compute='_compute_can_retry',
        help='True if job is in error state and retry count < 3',
    )

    is_final_state = fields.Boolean(
        string='Is Final State',
        compute='_compute_is_final_state',
        help='True if job is in done or failed state',
    )

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends('pdf_filename')
    def _compute_name(self):
        """Compute job name from ID and filename."""
        for job in self:
            job_id = job.id or 'New'
            filename = job.pdf_filename or 'Unnamed'
            job.name = f"Job #{job_id} - {filename}"

    @api.depends('state', 'retry_count')
    def _compute_can_retry(self):
        """Compute if retry is possible (error state and retries < 3)."""
        for job in self:
            job.can_retry = job.state == 'error' and job.retry_count < MAX_RETRIES

    @api.depends('state')
    def _compute_is_final_state(self):
        """Compute if job is in a final state (done or failed)."""
        for job in self:
            job.is_final_state = job.state in ('done', 'failed')

    @api.depends('retry_count')
    def _compute_next_retry_delay(self):
        """Compute next retry delay based on retry count (backoff pattern)."""
        for job in self:
            if job.retry_count < len(RETRY_DELAYS):
                job.next_retry_delay = RETRY_DELAYS[job.retry_count]
            else:
                job.next_retry_delay = RETRY_DELAYS[-1]

    # -------------------------------------------------------------------------
    # COPY METHOD
    # -------------------------------------------------------------------------

    def copy(self, default=None):
        """Override copy to reset state and ensure clean duplication.

        When duplicating an import job, we keep only the PDF file and filename.
        All processing results, relations, and state are reset to draft.

        Args:
            default (dict): Default values for the new record

        Returns:
            jsocr.import.job: New duplicated record
        """
        self.ensure_one()
        default = dict(default or {})

        # Force reset to draft state
        default.setdefault('state', 'draft')

        # Ensure detected_language is reset to default
        default.setdefault('detected_language', 'fr')

        return super().copy(default)

    # -------------------------------------------------------------------------
    # ACTION METHODS - State Machine
    # -------------------------------------------------------------------------

    def action_submit(self):
        """Submit job for processing (draft -> pending).

        Raises:
            UserError: If job is not in draft state.
        """
        for job in self:
            if job.state != 'draft':
                raise UserError(
                    f"Cannot submit job in state '{job.state}'. "
                    "Only draft jobs can be submitted."
                )
            job.state = 'pending'
            _logger.info("JSOCR: Job %s submitted (draft -> pending)", job.id)

    def action_process(self):
        """Start processing (pending -> processing).

        This method transitions the job to processing state. The actual
        OCR and AI processing is handled by external services.

        Raises:
            UserError: If job is not in pending state.
        """
        for job in self:
            if job.state != 'pending':
                raise UserError(
                    f"Cannot process job in state '{job.state}'. "
                    "Only pending jobs can be processed."
                )
            job.state = 'processing'
            _logger.info("JSOCR: Job %s processing started", job.id)

    def action_extract_text(self):
        """Extract text from PDF using OCR (button action).

        Can be called from the UI when job is in 'processing' state.
        Extracts text and detects language.

        Returns:
            dict: Notification action with result message
        """
        self.ensure_one()

        if self.state != 'processing':
            raise UserError(
                f"Cannot extract text for job in state '{self.state}'. "
                "Job must be in 'processing' state."
            )

        try:
            self._extract_text()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Extraction reussie',
                    'message': f'Langue detectee: {self.detected_language}. '
                               f'{len(self.extracted_text or "")} caracteres extraits.',
                    'type': 'success',
                    'sticky': False,
                }
            }
        except UserError:
            raise
        except Exception as e:
            _logger.error("JSOCR: Job %s extraction failed: %s", self.id, str(e))
            raise UserError(f"Extraction failed: {str(e)}")

    def action_mark_done(self):
        """Mark job as successfully completed (processing -> done).

        Called by the processing service when OCR and AI analysis
        complete successfully and the invoice is created.
        Also moves the PDF to success folder (Story 3.6).

        Raises:
            UserError: If job is not in processing state.
        """
        for job in self:
            if job.state != 'processing':
                raise UserError(
                    f"Cannot mark as done job in state '{job.state}'. "
                    "Only processing jobs can be marked done."
                )
            job.state = 'done'
            _logger.info("JSOCR: Job %s completed successfully", job.id)

            # Move PDF to success folder (Story 3.6)
            try:
                job._move_pdf_to_success()
            except Exception as e:
                _logger.error(
                    "JSOCR: Job %s failed to move PDF to success folder: %s",
                    job.id, type(e).__name__
                )

    def action_mark_error(self, error_message=None, error_type=None):
        """Mark job as error with optional message (processing -> error).

        Called by the processing service when an error occurs during
        OCR or AI analysis. The job can be retried up to 3 times.

        Args:
            error_message: Human-readable error description.
            error_type: Error category for retry logic (timeout, connection_error, etc.)

        Raises:
            UserError: If job is not in processing state.
        """
        for job in self:
            if job.state != 'processing':
                raise UserError(
                    f"Cannot mark as error job in state '{job.state}'. "
                    "Only processing jobs can be marked as error."
                )
            job.write({
                'state': 'error',
                'error_message': error_message or 'Unknown error occurred',
            })
            _logger.warning(
                "JSOCR: Job %s failed with error (type=%s): %s",
                job.id, error_type or 'unknown', error_message or 'No message'
            )

    def action_retry(self):
        """Retry after error (error -> pending).

        Increments retry counter and resets to pending state.
        Uses backoff delays: 5s, 15s, 30s for scheduling.

        Raises:
            UserError: If job is not in error state or max retries reached.
        """
        for job in self:
            if job.state != 'error':
                raise UserError(
                    f"Cannot retry job in state '{job.state}'. "
                    "Only jobs in error state can be retried."
                )
            if job.retry_count >= MAX_RETRIES:
                raise UserError(
                    f"Maximum retry attempts ({MAX_RETRIES}) reached for job {job.id}. "
                    "Please mark as failed or investigate the issue."
                )
            new_retry_count = job.retry_count + 1
            delay = RETRY_DELAYS[job.retry_count] if job.retry_count < len(RETRY_DELAYS) else RETRY_DELAYS[-1]
            job.write({
                'state': 'pending',
                'retry_count': new_retry_count,
                'error_message': False,
            })
            _logger.info(
                "JSOCR: Job %s retrying (attempt %d of %d, delay was %ds)",
                job.id, new_retry_count, MAX_RETRIES, delay
            )

    def action_mark_failed(self):
        """Mark as definitive failure (error -> failed).

        Called when the job should not be retried anymore, either
        manually or after max retries exceeded.
        Also moves the PDF to error folder and sends alert email (Story 3.7).

        Raises:
            UserError: If job is not in error state.
        """
        for job in self:
            if job.state != 'error':
                raise UserError(
                    f"Cannot mark as failed job in state '{job.state}'. "
                    "Only jobs in error state can be marked as failed."
                )
            job.state = 'failed'
            _logger.warning("JSOCR: Job %s marked as failed", job.id)

            # Move PDF to error folder (Story 3.7)
            try:
                job._move_pdf_to_error()
            except Exception as e:
                _logger.error(
                    "JSOCR: Job %s failed to move PDF to error folder: %s",
                    job.id, type(e).__name__
                )

            # Send failure alert email (Story 3.7)
            try:
                job._send_failure_alert()
            except Exception as e:
                _logger.error(
                    "JSOCR: Job %s failed to send failure alert: %s",
                    job.id, type(e).__name__
                )

    def action_cancel(self):
        """Cancel job and reset to draft.

        Resets state and retry counter. Cannot cancel jobs in final states.

        Raises:
            UserError: If job is in done or failed state.
        """
        for job in self:
            if job.state in ('done', 'failed'):
                raise UserError(
                    f"Cannot cancel job in final state '{job.state}'. "
                    "Jobs that are done or failed cannot be cancelled."
                )
            job.write({
                'state': 'draft',
                'retry_count': 0,
                'error_message': False,
            })
            _logger.info("JSOCR: Job %s cancelled", job.id)

    # -------------------------------------------------------------------------
    # HELPER METHODS
    # -------------------------------------------------------------------------

    def _should_retry(self, error_type):
        """Check if job should be retried based on error type.

        Args:
            error_type: Type of error (timeout, connection_error, etc.)

        Returns:
            bool: True if retry is possible and recommended for this error type.
        """
        self.ensure_one()
        retryable_errors = ['timeout', 'connection_error', 'service_unavailable']
        return (
            self.state == 'error' and
            error_type in retryable_errors and
            self.retry_count < MAX_RETRIES
        )

    def _get_retry_delay(self):
        """Get the delay in seconds for the next retry attempt.

        Returns:
            int: Delay in seconds based on retry_count (5, 15, or 30).
        """
        self.ensure_one()
        if self.retry_count < len(RETRY_DELAYS):
            return RETRY_DELAYS[self.retry_count]
        return RETRY_DELAYS[-1]

    # -------------------------------------------------------------------------
    # OCR EXTRACTION METHODS
    # -------------------------------------------------------------------------

    def _extract_text(self):
        """Extract text from PDF using OCR service.

        Uses OCRService to extract text from the job's PDF file and stores
        the result in the extracted_text field. Also detects and stores
        the document language.

        Returns:
            str: Extracted text from PDF

        Raises:
            UserError: If PDF file is missing or extraction fails
        """
        self.ensure_one()

        if not self.pdf_file:
            raise UserError("Cannot extract text: PDF file is missing")

        _logger.info("JSOCR: Job %s starting text extraction", self.id)

        try:
            # Import OCR service
            from odoo.addons.js_invoice_ocr_ia.services.ocr_service import OCRService

            # Decode base64 PDF to bytes
            pdf_binary = base64.b64decode(self.pdf_file)

            # Extract text using OCR service
            ocr = OCRService()
            extracted_text = ocr.extract_text_from_pdf(pdf_binary)

            # Detect language from extracted text (Story 3.3)
            detected_lang = ocr.detect_language(extracted_text)

            # Store results
            self.write({
                'extracted_text': extracted_text,
                'detected_language': detected_lang,
            })

            _logger.info("JSOCR: Job %s text extraction complete (lang=%s)", self.id, detected_lang)
            return extracted_text

        except ValueError as e:
            error_msg = str(e)
            _logger.error("JSOCR: Job %s extraction failed: %s", self.id, type(e).__name__)
            raise UserError(f"Text extraction failed: {error_msg}") from e
        except Exception as e:
            _logger.error("JSOCR: Job %s unexpected extraction error: %s", self.id, type(e).__name__)
            raise UserError(f"Unexpected error during text extraction: {type(e).__name__}") from e

    # -------------------------------------------------------------------------
    # FILE MOVEMENT METHODS (Story 3.6, 3.7)
    # -------------------------------------------------------------------------

    def _move_pdf_to_success(self):
        """Move PDF to success folder with timestamp prefix (Story 3.6).

        Copies the PDF content from the binary field to the success folder.
        The filename is prefixed with timestamp (YYYYMMDD_HHMMSS_).
        Files are never deleted, only archived (NFR12).
        """
        self.ensure_one()

        if not self.pdf_file:
            _logger.warning("JSOCR: Job %s has no PDF file to move", self.id)
            return

        config = self.env['jsocr.config'].get_config()
        if not config.success_folder_path:
            _logger.warning("JSOCR: Success folder not configured")
            return

        success_path = Path(config.success_folder_path)

        # Ensure folder exists
        if not success_path.exists():
            success_path.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dest_name = f"{timestamp}_{self.pdf_filename}"
        dest_path = success_path / dest_name

        # Write PDF content to file
        pdf_content = base64.b64decode(self.pdf_file)
        dest_path.write_bytes(pdf_content)

        _logger.info("JSOCR: Job %s PDF moved to success: %s", self.id, dest_name)

    def _move_pdf_to_error(self):
        """Move PDF to error folder with timestamp prefix (Story 3.7).

        Copies the PDF content from the binary field to the error folder.
        The filename is prefixed with timestamp (YYYYMMDD_HHMMSS_).
        """
        self.ensure_one()

        if not self.pdf_file:
            _logger.warning("JSOCR: Job %s has no PDF file to move", self.id)
            return

        config = self.env['jsocr.config'].get_config()
        if not config.error_folder_path:
            _logger.warning("JSOCR: Error folder not configured")
            return

        error_path = Path(config.error_folder_path)

        # Ensure folder exists
        if not error_path.exists():
            error_path.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dest_name = f"{timestamp}_{self.pdf_filename}"
        dest_path = error_path / dest_name

        # Write PDF content to file
        pdf_content = base64.b64decode(self.pdf_file)
        dest_path.write_bytes(pdf_content)

        _logger.info("JSOCR: Job %s PDF moved to error: %s", self.id, dest_name)

    def _send_failure_alert(self):
        """Send email alert for failed job (Story 3.7).

        Sends notification email to alert_email if configured.
        Includes filename and error message in the email body.
        """
        self.ensure_one()

        config = self.env['jsocr.config'].get_config()
        if not config.alert_email:
            return

        error_detail = self.error_message or 'Aucun detail disponible'

        mail_values = {
            'subject': f'JSOCR: Echec traitement - {self.pdf_filename}',
            'body_html': f'''<p>Le traitement du fichier <b>{self.pdf_filename}</b> a echoue.</p>
<p>Job ID: {self.id}</p>
<p>Erreur: {error_detail}</p>''',
            'email_to': config.alert_email,
        }

        try:
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.send()
            _logger.info("JSOCR: Job %s failure alert email sent", self.id)
        except Exception as e:
            _logger.error("JSOCR: Job %s failed to send alert email: %s", self.id, type(e).__name__)

    # -------------------------------------------------------------------------
    # AI ANALYSIS METHODS (Story 4.1-4.7)
    # -------------------------------------------------------------------------

    def action_analyze_with_ai(self):
        """Analyze extracted text with AI to extract invoice data (button action).

        Can be called from the UI when job is in 'processing' state and has extracted text.
        Extracts structured data and stores in job fields.

        Returns:
            dict: Notification action with result message
        """
        self.ensure_one()

        if self.state != 'processing':
            raise UserError(
                f"Cannot analyze job in state '{self.state}'. "
                "Job must be in 'processing' state."
            )

        if not self.extracted_text:
            raise UserError(
                "Cannot analyze: no extracted text. "
                "Please run OCR extraction first."
            )

        try:
            result = self._analyze_with_ai()
            if result.get('success'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Analyse IA reussie',
                        'message': f"Fournisseur detecte: {self.extracted_supplier_name or 'Non trouve'}",
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Echec analyse IA',
                        'message': result.get('error', 'Erreur inconnue'),
                        'type': 'warning',
                        'sticky': True,
                    }
                }
        except Exception as e:
            _logger.error("JSOCR: Job %s AI analysis failed: %s", self.id, str(e))
            raise UserError(f"AI analysis failed: {str(e)}")

    def _analyze_with_ai(self):
        """Perform AI analysis on extracted text.

        Uses OllamaService to extract structured invoice data.

        Returns:
            dict: Result with 'success' key and extracted data
        """
        self.ensure_one()

        _logger.info("JSOCR: Job %s starting AI analysis", self.id)

        # Get config
        config = self.env['jsocr.config'].get_config()

        # Initialize Ollama service
        from odoo.addons.js_invoice_ocr_ia.services.ai_service import OllamaService

        ollama = OllamaService(
            url=config.ollama_url,
            model=config.ollama_model,
            timeout=config.ollama_timeout,
        )

        # Extract data
        result = ollama.extract_invoice_data(
            self.extracted_text,
            language=self.detected_language or 'fr'
        )

        if not result.get('success'):
            _logger.warning("JSOCR: Job %s AI extraction failed: %s", self.id, result.get('error'))
            return result

        data = result.get('data', {})
        confidence_data = result.get('confidence_data', {})

        # Store raw AI response
        self.ai_response = result.get('raw_response', '')
        self.confidence_data = json.dumps(confidence_data) if confidence_data else ''

        # Extract and store individual fields (Story 4.3-4.6)
        self._store_extracted_data(data, ollama)

        _logger.info("JSOCR: Job %s AI analysis complete", self.id)
        return result

    def _store_extracted_data(self, data, ollama_service):
        """Store extracted data in job fields.

        Args:
            data (dict): Extracted data from AI
            ollama_service: OllamaService instance for parsing
        """
        self.ensure_one()

        # Supplier (Story 4.3)
        supplier_name = data.get('supplier_name')
        self.extracted_supplier_name = supplier_name

        # Find matching Odoo partner
        if supplier_name:
            partner = ollama_service.find_supplier(self.env, supplier_name)
            if partner:
                self.partner_id = partner.id

        # Date (Story 4.4)
        date_str = data.get('invoice_date')
        parsed_date = ollama_service.parse_invoice_date(date_str)
        if parsed_date:
            self.extracted_invoice_date = parsed_date

        # Invoice number (Story 4.4)
        self.extracted_invoice_number = data.get('invoice_number')

        # Lines (Story 4.5)
        lines = ollama_service.parse_invoice_lines(data.get('lines', []))
        self.extracted_lines = json.dumps(lines) if lines else ''

        # Amounts (Story 4.6)
        self.extracted_amount_untaxed = ollama_service._parse_amount(data.get('amount_untaxed')) or 0.0
        self.extracted_amount_tax = ollama_service._parse_amount(data.get('amount_tax')) or 0.0
        self.extracted_amount_total = ollama_service._parse_amount(data.get('amount_total')) or 0.0

    # -------------------------------------------------------------------------
    # INVOICE CREATION METHODS (Story 4.8-4.10)
    # -------------------------------------------------------------------------

    def action_create_invoice(self):
        """Create draft supplier invoice from extracted data (button action).

        Can be called from UI when job is in 'processing' state.

        Returns:
            dict: Action to open the created invoice
        """
        self.ensure_one()

        if self.state != 'processing':
            raise UserError(
                f"Cannot create invoice for job in state '{self.state}'. "
                "Job must be in 'processing' state."
            )

        if self.invoice_id:
            raise UserError(
                "Invoice already exists for this job. "
                "Please delete it first if you want to recreate."
            )

        try:
            invoice = self._create_draft_invoice()
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'current',
            }
        except Exception as e:
            _logger.error("JSOCR: Job %s invoice creation failed: %s", self.id, str(e))
            raise UserError(f"Invoice creation failed: {str(e)}")

    def _create_draft_invoice(self):
        """Create a draft supplier invoice from extracted data (Story 4.8).

        Creates account.move with type 'in_invoice' in draft state.
        Associates partner if found, fills date and supplier reference.
        Requirement: NFR4 - creation < 5 seconds

        Returns:
            account.move: Created invoice record
        """
        self.ensure_one()

        _logger.info("JSOCR: Job %s creating draft invoice", self.id)

        # Prepare invoice values
        invoice_vals = {
            'move_type': 'in_invoice',
            'state': 'draft',
            'jsocr_import_job_id': self.id,
        }

        # Partner (Story 4.8 - FR19)
        if self.partner_id:
            invoice_vals['partner_id'] = self.partner_id.id

        # Date (invoice_date = document date, date = accounting date)
        if self.extracted_invoice_date:
            invoice_vals['invoice_date'] = self.extracted_invoice_date
            invoice_vals['date'] = self.extracted_invoice_date

        # Supplier reference (invoice number)
        if self.extracted_invoice_number:
            invoice_vals['ref'] = self.extracted_invoice_number

        # Create invoice
        invoice = self.env['account.move'].create(invoice_vals)
        _logger.info("JSOCR: Job %s created invoice %s", self.id, invoice.id)

        # Add invoice lines (Story 4.9)
        self._create_invoice_lines(invoice)

        # Validate total after lines creation (HT/TTC validation)
        self._validate_invoice_total(invoice)

        # Attach PDF source (Story 4.10)
        self._attach_pdf_to_invoice(invoice)

        # Store confidence data on invoice
        if self.confidence_data:
            invoice.jsocr_confidence_data = self.confidence_data

        # Link invoice to job
        self.invoice_id = invoice.id

        return invoice

    def _create_invoice_lines(self, invoice):
        """Create invoice lines from extracted data (Story 4.9 - FR20).

        Uses intelligent account prediction based on:
        1. Learned patterns (jsocr.account.pattern)
        2. Historical invoice lines from last 10 invoices
        3. Supplier's default charge account (fallback)
        4. Generic expense account (last resort)

        Also performs HT/TTC detection and price adjustment based on tax expectations.

        Lines are created via invoice_line_ids command tuples to ensure
        proper Odoo 18 compute field triggering.

        Args:
            invoice: account.move record
        """
        self.ensure_one()

        if not self.extracted_lines:
            _logger.info("JSOCR: Job %s no lines to create", self.id)
            return

        try:
            lines = json.loads(self.extracted_lines)
        except (json.JSONDecodeError, TypeError):
            _logger.warning("JSOCR: Job %s invalid lines JSON", self.id)
            return

        if not lines:
            return

        # Fallback account
        fallback_account_id = self._get_expense_account()
        if not fallback_account_id:
            _logger.warning("JSOCR: Job %s no expense account found, skipping lines", self.id)
            return

        # Detect amounts type (HT/TTC) BEFORE creating lines
        amounts_type = self._detect_amounts_type(lines)
        if amounts_type == 'unknown':
            _logger.warning("JSOCR: Job %s HT/TTC detection inconclusive", self.id)
            invoice.jsocr_amount_mismatch = True

        # Get historical data for prediction (Story 4.16)
        historical_lines = []
        if self.partner_id:
            try:
                historical_lines = self._get_historical_lines_data(self.partner_id.id)
            except Exception as e:
                _logger.warning("JSOCR: Job %s history retrieval failed: %s", self.id, e)

        # Build line commands for invoice_line_ids (Odoo 18 ORM pattern)
        line_commands = []
        for line in lines:
            description = line.get('description', 'Ligne facture')

            # Predict account for this line (Story 4.17)
            try:
                account_id, confidence, source = self._predict_line_account(
                    self.partner_id.id if self.partner_id else None,
                    description,
                    historical_lines,
                    fallback_account_id,
                )
            except Exception as e:
                _logger.warning("JSOCR: Job %s prediction failed for line: %s", self.id, e)
                account_id = fallback_account_id
                confidence = 10
                source = 'default'

            # Get original price
            original_price = line.get('unit_price', 0.0)

            # Get tax info for predicted account and adjust price if needed
            tax_info = self._get_tax_for_account(account_id)
            adjusted_price, was_adjusted = self._adjust_price_unit(
                original_price, amounts_type, tax_info
            )

            line_vals = {
                'name': description,
                'quantity': line.get('quantity', 1.0),
                'price_unit': adjusted_price,
                'account_id': account_id,
                'jsocr_account_confidence': confidence,
                'jsocr_account_source': source,
                'jsocr_predicted_account_id': account_id,
            }
            line_commands.append((0, 0, line_vals))

        if line_commands:
            invoice.write({'invoice_line_ids': line_commands})
            _logger.info("JSOCR: Job %s created %d invoice lines", self.id, len(line_commands))

    def _get_expense_account(self):
        """Get the expense account to use for invoice lines.

        Priority:
        1. Supplier's default JSOCR account
        2. Generic expense account

        Returns:
            int or None: account.account ID
        """
        self.ensure_one()

        # Check supplier's default account
        if self.partner_id and self.partner_id.jsocr_default_account_id:
            return self.partner_id.jsocr_default_account_id.id

        # Find generic expense account (6xxx in Swiss plan)
        # Filter by account_type to exclude Outstanding Receipts/Payments
        # Note: In Odoo 18, account.account no longer has company_id field
        expense_account = self.env['account.account'].search([
            ('code', '=like', '6%'),
            ('account_type', 'in', ('expense', 'expense_depreciation', 'expense_direct_cost')),
        ], order='code', limit=1)

        if expense_account:
            return expense_account.id

        # Fallback: any expense account regardless of code
        expense_account = self.env['account.account'].search([
            ('account_type', 'in', ('expense', 'expense_depreciation', 'expense_direct_cost')),
        ], order='code', limit=1)

        return expense_account.id if expense_account else None

    # -------------------------------------------------------------------------
    # ACCOUNT PREDICTION METHODS (Story 4.16, 4.17)
    # -------------------------------------------------------------------------

    def _get_supplier_invoice_history(self, partner_id, limit=10):
        """Get last N posted invoices for a supplier (Story 4.16).

        Args:
            partner_id (int): Supplier partner ID
            limit (int): Max number of invoices to retrieve (default 10)

        Returns:
            account.move recordset: Posted supplier invoices ordered by date desc
        """
        return self.env['account.move'].search([
            ('partner_id', '=', partner_id),
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted'),
        ], order='invoice_date desc, id desc', limit=limit)

    def _get_historical_lines_data(self, partner_id):
        """Extract all lines with description and account from supplier history (Story 4.16).

        Retrieves line descriptions and their associated expense accounts from
        the last 10 posted invoices for the given supplier.

        Args:
            partner_id (int): Supplier partner ID

        Returns:
            list[dict]: List of {description, account_id, account_code, normalized}
        """
        invoices = self._get_supplier_invoice_history(partner_id)
        if not invoices:
            return []

        PatternModel = self.env['jsocr.account.pattern']
        result = []

        for invoice in invoices:
            for line in invoice.invoice_line_ids:
                if not line.account_id or not line.name:
                    continue
                # Only consider expense-type accounts
                if line.account_id.account_type not in (
                    'expense', 'expense_depreciation', 'expense_direct_cost'
                ):
                    continue

                result.append({
                    'description': line.name,
                    'account_id': line.account_id.id,
                    'account_code': line.account_id.code,
                    'normalized': PatternModel.normalize_text(line.name),
                })

        _logger.info(
            "JSOCR: Found %d historical lines for partner %s",
            len(result), partner_id
        )
        return result

    def _predict_line_account(self, partner_id, description, historical_lines, fallback_account_id):
        """Predict the best account for a line description (Story 4.17).

        Priority:
        1. Exact/partial match from jsocr.account.pattern (learned patterns)
        2. Similarity matching against historical invoice lines
        3. Fallback to default expense account

        Args:
            partner_id (int or None): Supplier partner ID
            description (str): Line description to match
            historical_lines (list[dict]): Historical data from _get_historical_lines_data
            fallback_account_id (int): Fallback account ID

        Returns:
            tuple: (account_id, confidence, source)
                - account_id (int): Predicted account ID
                - confidence (int): Confidence score 0-100
                - source (str): 'pattern', 'history', or 'default'
        """
        if not partner_id or not description:
            return fallback_account_id, 10, 'default'

        # Step 1: Check learned patterns (Story 4.18)
        PatternModel = self.env['jsocr.account.pattern']
        account_id, confidence, source = PatternModel.find_matching_pattern(
            partner_id, description
        )
        if account_id and confidence >= 30:
            return account_id, confidence, source

        # Step 2: Match against historical lines (Story 4.17)
        if historical_lines:
            account_id, confidence = self._match_description_to_history(
                description, historical_lines
            )
            if account_id and confidence >= 30:
                return account_id, confidence, 'history'

        # Step 3: Fallback
        return fallback_account_id, 10, 'default'

    # -------------------------------------------------------------------------
    # HT/TTC DETECTION AND CONVERSION METHODS
    # -------------------------------------------------------------------------

    def _detect_amounts_type(self, lines):
        """Detect if extracted amounts are HT (untaxed) or TTC (tax-included).

        Compares sum of (unit_price * quantity) against extracted totals.
        Uses absolute values to handle credit notes with negative quantities.

        Args:
            lines (list[dict]): Extracted invoice lines with 'unit_price' and 'quantity'

        Returns:
            str: 'ht' if amounts match untaxed total, 'ttc' if match total,
                 'unknown' if no match or data insufficient
        """
        self.ensure_one()

        # Guard clause: empty lines
        if not lines:
            _logger.debug("JSOCR: Job %s _detect_amounts_type: no lines", self.id)
            return 'unknown'

        # Calculate sum of line amounts (absolute values for credit notes)
        sum_lines = sum(
            abs(line.get('unit_price', 0.0) * line.get('quantity', 1.0))
            for line in lines
        )

        # Guard clause: no extracted totals
        untaxed = self.extracted_amount_untaxed or 0.0
        total = self.extracted_amount_total or 0.0

        if untaxed == 0.0 and total == 0.0:
            _logger.debug("JSOCR: Job %s _detect_amounts_type: no extracted totals", self.id)
            return 'unknown'

        tolerance = 0.03

        # Compare with untaxed first (HT) - explicit order per spec
        if untaxed > 0.0 and abs(sum_lines - untaxed) <= tolerance:
            _logger.info(
                "JSOCR: Job %s detected amounts as HT (sum=%.2f, untaxed=%.2f)",
                self.id, sum_lines, untaxed
            )
            return 'ht'

        # Then compare with total (TTC)
        if total > 0.0 and abs(sum_lines - total) <= tolerance:
            _logger.info(
                "JSOCR: Job %s detected amounts as TTC (sum=%.2f, total=%.2f)",
                self.id, sum_lines, total
            )
            return 'ttc'

        # No match
        _logger.warning(
            "JSOCR: Job %s amounts type unknown (sum=%.2f, untaxed=%.2f, total=%.2f)",
            self.id, sum_lines, untaxed, total
        )
        return 'unknown'

    def _get_tax_for_account(self, account_id):
        """Get tax information for a given account.

        Reads the account's default taxes and determines:
        - Combined tax rate (sum of all purchase tax rates)
        - Whether taxes expect TTC amounts (price_include_override or price_include)

        Args:
            account_id (int or None): Account ID to check

        Returns:
            dict or None: {'tax_expects_ttc': bool, 'tax_rate': float} or None if no taxes
        """
        self.ensure_one()

        # Guard clause: invalid account_id
        if not account_id:
            return None

        account = self.env['account.account'].browse(account_id)

        # Guard clause: account doesn't exist
        if not account.exists():
            return None

        # Filter for purchase taxes
        purchase_taxes = account.tax_ids.filtered(
            lambda t: t.type_tax_use in ('purchase', 'none')
        )

        if not purchase_taxes:
            return None

        # Calculate combined tax rate (F3 - multi-taxes)
        total_rate = sum(tax.amount for tax in purchase_taxes)

        # Determine if any tax expects TTC (F8 - fallback on price_include)
        any_tax_expects_ttc = any(
            tax.price_include_override == 'tax_included'
            or (not tax.price_include_override and tax.price_include)
            for tax in purchase_taxes
        )

        _logger.debug(
            "JSOCR: Account %s tax info: rate=%.2f%%, expects_ttc=%s",
            account_id, total_rate, any_tax_expects_ttc
        )

        return {
            'tax_expects_ttc': any_tax_expects_ttc,
            'tax_rate': total_rate,
        }

    def _adjust_price_unit(self, price_unit, amounts_type, tax_info):
        """Adjust price_unit based on amounts type and tax expectations.

        Converts:
        - HT to TTC if tax expects TTC: price * (1 + rate/100)
        - TTC to HT if tax expects HT: price / (1 + rate/100)

        Args:
            price_unit (float): Original price from extraction
            amounts_type (str): 'ht', 'ttc', or 'unknown'
            tax_info (dict or None): From _get_tax_for_account

        Returns:
            tuple: (adjusted_price, was_adjusted)
        """
        # No tax info - no adjustment
        if tax_info is None:
            return (price_unit, False)

        # Unknown type - no adjustment
        if amounts_type == 'unknown':
            return (price_unit, False)

        # Guard clause: division by zero (F1)
        divisor = 1 + tax_info['tax_rate'] / 100
        if divisor <= 0:
            _logger.warning(
                "JSOCR: Invalid tax rate %.2f, skipping conversion",
                tax_info['tax_rate']
            )
            return (price_unit, False)

        original_price = price_unit
        was_adjusted = False

        # Only convert if tax rate > 0 (0% tax means no actual conversion needed)
        if tax_info['tax_rate'] > 0:
            # HT amounts but tax expects TTC -> convert to TTC
            if amounts_type == 'ht' and tax_info['tax_expects_ttc']:
                price_unit = price_unit * divisor
                was_adjusted = True

            # TTC amounts but tax expects HT -> convert to HT
            elif amounts_type == 'ttc' and not tax_info['tax_expects_ttc']:
                price_unit = price_unit / divisor
                was_adjusted = True

        # Round to 2 decimals
        price_unit = round(price_unit, 2)

        if was_adjusted:
            _logger.info(
                "JSOCR: Adjusted price %.2f -> %.2f (type=%s, tax_rate=%.2f%%, expects_ttc=%s)",
                original_price, price_unit, amounts_type,
                tax_info['tax_rate'], tax_info['tax_expects_ttc']
            )

        return (price_unit, was_adjusted)

    def _validate_invoice_total(self, invoice):
        """Validate computed invoice total against extracted total.

        Compares invoice.amount_total with extracted_amount_total using
        fixed tolerance of 0.03.

        Args:
            invoice: account.move record

        Returns:
            bool: True if valid (within tolerance or no reference), False if mismatch
        """
        self.ensure_one()

        # Guard clause: no extracted total (F6)
        if not self.extracted_amount_total:
            _logger.debug("JSOCR: Job %s no extracted_amount_total for validation", self.id)
            return True

        ecart = abs(invoice.amount_total - self.extracted_amount_total)
        tolerance = 0.03

        if ecart <= tolerance:
            _logger.debug(
                "JSOCR: Job %s total validation OK (computed=%.2f, extracted=%.2f, ecart=%.2f)",
                self.id, invoice.amount_total, self.extracted_amount_total, ecart
            )
            # Reset mismatch flag if validation passes (may have been set by unknown detection)
            invoice.jsocr_amount_mismatch = False
            return True

        # Mismatch detected
        _logger.warning(
            "JSOCR: Job %s total mismatch (computed=%.2f, extracted=%.2f, ecart=%.2f)",
            self.id, invoice.amount_total, self.extracted_amount_total, ecart
        )

        invoice.jsocr_amount_mismatch = True

        # Calculate confidence: 50 if small ecart, 30 if larger
        confidence = 50 if ecart < 1.0 else 30
        if not invoice.set_field_confidence('total', self.extracted_amount_total, confidence):
            _logger.warning("JSOCR: Job %s failed to set confidence for total", self.id)

        return False

    def _match_description_to_history(self, description, historical_lines):
        """Match a description against historical lines using similarity (Story 4.17).

        Uses normalized keyword comparison (Jaccard similarity) to find
        the best matching account from historical invoice lines.

        Args:
            description (str): Current line description
            historical_lines (list[dict]): Historical data with 'normalized' and 'account_id'

        Returns:
            tuple: (account_id, confidence) or (None, 0)
        """
        PatternModel = self.env['jsocr.account.pattern']
        normalized_desc = PatternModel.normalize_text(description)

        if not normalized_desc:
            return None, 0

        search_words = set(normalized_desc.split())
        if not search_words:
            return None, 0

        # Calculate similarity for each historical line
        matches = []  # list of (similarity, account_id)

        for hist_line in historical_lines:
            hist_normalized = hist_line.get('normalized', '')
            if not hist_normalized:
                continue

            hist_words = set(hist_normalized.split())
            if not hist_words:
                continue

            # Jaccard similarity
            intersection = len(search_words & hist_words)
            union = len(search_words | hist_words)

            if union > 0:
                similarity = intersection / union
                if similarity > 0.3:  # Minimum threshold
                    matches.append((similarity, hist_line['account_id']))

        if not matches:
            return None, 0

        # Count account frequency among matches, weighted by similarity
        account_scores = {}
        for similarity, account_id in matches:
            if account_id not in account_scores:
                account_scores[account_id] = {'count': 0, 'total_sim': 0.0}
            account_scores[account_id]['count'] += 1
            account_scores[account_id]['total_sim'] += similarity

        # Find the best account (highest weighted score)
        best_account_id = None
        best_score = 0

        total_matches = len(matches)
        for account_id, data in account_scores.items():
            # Score = frequency ratio * average similarity
            frequency_ratio = data['count'] / total_matches
            avg_similarity = data['total_sim'] / data['count']
            score = frequency_ratio * avg_similarity

            if score > best_score:
                best_score = score
                best_account_id = account_id

        if best_account_id:
            # Confidence based on number of matches and score quality
            confidence = int(min(
                30 + (min(total_matches, 5) * 10) + (best_score * 20),
                95
            ))
            _logger.info(
                "JSOCR: History match found, account=%s, confidence=%d, matches=%d",
                best_account_id, confidence, total_matches
            )
            return best_account_id, confidence

        return None, 0

    def _attach_pdf_to_invoice(self, invoice):
        """Attach source PDF to the created invoice (Story 4.10 - FR21).

        Creates ir.attachment linked to the invoice so the PDF is
        visible natively in Odoo's attachment panel.

        Args:
            invoice: account.move record
        """
        self.ensure_one()

        if not self.pdf_file:
            _logger.warning("JSOCR: Job %s no PDF file to attach", self.id)
            return

        # Create attachment
        attachment_vals = {
            'name': self.pdf_filename or 'source.pdf',
            'type': 'binary',
            'datas': self.pdf_file,
            'res_model': 'account.move',
            'res_id': invoice.id,
            'mimetype': 'application/pdf',
        }

        self.env['ir.attachment'].create(attachment_vals)
        _logger.info("JSOCR: Job %s attached PDF to invoice %s", self.id, invoice.id)

    # -------------------------------------------------------------------------
    # FULL PROCESSING WORKFLOW (Story 4.11-4.12)
    # -------------------------------------------------------------------------

    def action_process_full(self):
        """Process job completely: OCR, AI analysis, and invoice creation.

        Button action that runs the full pipeline in one click.

        Returns:
            dict: Action to open the created invoice or notification
        """
        self.ensure_one()

        if self.state not in ('pending', 'processing'):
            raise UserError(
                f"Cannot process job in state '{self.state}'. "
                "Job must be in 'pending' or 'processing' state."
            )

        try:
            # Transition to processing if needed
            if self.state == 'pending':
                self.action_process()

            # Step 1: Extract text
            if not self.extracted_text:
                self._extract_text()

            # Step 2: AI analysis
            ai_result = self._analyze_with_ai()
            if not ai_result.get('success'):
                error_type = ai_result.get('error_type', 'unknown')
                if self._should_retry(error_type):
                    self.action_mark_error(
                        error_message=ai_result.get('error'),
                        error_type=error_type
                    )
                    self.action_retry()
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Erreur - Nouvelle tentative',
                            'message': f"Erreur: {ai_result.get('error')}. Nouvelle tentative programmee.",
                            'type': 'warning',
                            'sticky': True,
                        }
                    }
                else:
                    self.action_mark_error(
                        error_message=ai_result.get('error'),
                        error_type=error_type
                    )
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Echec traitement',
                            'message': ai_result.get('error'),
                            'type': 'danger',
                            'sticky': True,
                        }
                    }

            # Step 3: Create invoice
            invoice = self._create_draft_invoice()

            # Step 4: Mark as done
            self.action_mark_done()

            # Step 5: Send notification (Story 4.15)
            self._send_invoice_ready_notification()

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'current',
            }

        except UserError:
            raise
        except Exception as e:
            _logger.error("JSOCR: Job %s full processing failed: %s", self.id, str(e))
            self.action_mark_error(
                error_message=str(e),
                error_type='processing_error'
            )
            raise UserError(f"Processing failed: {str(e)}")

    def _process_job_async(self):
        """Process job in background (for queue_job integration - Story 4.11).

        This method is designed to be called by queue_job. It handles the
        full processing pipeline and properly manages errors and retries.

        Note: queue_job will be fully integrated when the dependency is uncommented.
        """
        self.ensure_one()

        _logger.info("JSOCR: Job %s starting async processing", self.id)

        try:
            # Transition to processing
            if self.state == 'pending':
                self.state = 'processing'

            # Step 1: Extract text
            if not self.extracted_text:
                self._extract_text()

            # Step 2: AI analysis
            ai_result = self._analyze_with_ai()
            if not ai_result.get('success'):
                error_type = ai_result.get('error_type', 'unknown')
                self._handle_processing_error(ai_result.get('error'), error_type)
                return

            # Step 3: Create invoice
            self._create_draft_invoice()

            # Step 4: Mark as done
            self.state = 'done'
            _logger.info("JSOCR: Job %s async processing completed", self.id)

            # Move PDF to success folder
            try:
                self._move_pdf_to_success()
            except Exception as e:
                _logger.error("JSOCR: Job %s failed to move PDF: %s", self.id, type(e).__name__)

            # Send notification
            self._send_invoice_ready_notification()

        except Exception as e:
            _logger.error("JSOCR: Job %s async processing error: %s", self.id, str(e))
            self._handle_processing_error(str(e), 'processing_error')

    def _handle_processing_error(self, error_message, error_type):
        """Handle processing errors with retry logic (Story 4.12).

        Implements the retry pattern: 3 attempts with backoff (5s, 15s, 30s).
        Permanent errors (parse_error) go directly to 'error' state.

        Args:
            error_message (str): Error description
            error_type (str): Error category for retry decision
        """
        self.ensure_one()

        permanent_errors = ['parse_error', 'validation_error']

        if error_type in permanent_errors:
            # Permanent error - go directly to error state
            self.write({
                'state': 'error',
                'error_message': error_message,
            })
            _logger.warning(
                "JSOCR: Job %s permanent error (type=%s): %s",
                self.id, error_type, error_message
            )
        elif self.retry_count < MAX_RETRIES:
            # Transient error - can retry
            new_retry_count = self.retry_count + 1
            self.write({
                'state': 'pending',  # Back to pending for retry
                'retry_count': new_retry_count,
                'error_message': f"Retry {new_retry_count}/{MAX_RETRIES}: {error_message}",
            })
            _logger.info(
                "JSOCR: Job %s scheduled for retry %d/%d",
                self.id, new_retry_count, MAX_RETRIES
            )
        else:
            # Max retries exceeded
            self.write({
                'state': 'failed',
                'error_message': f"Max retries exceeded: {error_message}",
            })
            _logger.warning("JSOCR: Job %s failed after %d retries", self.id, MAX_RETRIES)

            # Move PDF to error folder and send alert
            try:
                self._move_pdf_to_error()
            except Exception:
                pass
            try:
                self._send_failure_alert()
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # NOTIFICATION METHODS (Story 4.15)
    # -------------------------------------------------------------------------

    def _send_invoice_ready_notification(self):
        """Send Odoo notification when invoice is ready (Story 4.15 - FR35).

        Sends a system notification to the user who will validate the invoice.
        The notification is clickable and opens the invoice list.
        """
        self.ensure_one()

        if not self.invoice_id:
            return

        # Send activity/notification to users with OCR rights
        try:
            # Post a message in the chatter
            self.message_post(
                body=f"Facture brouillon creee: {self.invoice_id.name or 'Nouveau'}",
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

            # Create activity for invoice validation
            if self.invoice_id:
                activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                if activity_type:
                    self.invoice_id.activity_schedule(
                        activity_type_id=activity_type.id,
                        summary='Facture OCR a valider',
                        note=f'Cette facture a ete creee automatiquement depuis le fichier {self.pdf_filename}.',
                        user_id=self.env.user.id,
                    )

            _logger.info("JSOCR: Job %s notification sent", self.id)

        except Exception as e:
            _logger.error("JSOCR: Job %s failed to send notification: %s", self.id, type(e).__name__)

    # -------------------------------------------------------------------------
    # CRON METHODS (Story 4.11)
    # -------------------------------------------------------------------------

    @api.model
    def cron_process_pending_jobs(self):
        """Cron method to process pending jobs.

        Called by ir.cron to process jobs that are in 'pending' state.
        Processes jobs one by one to respect NFR10 (one failure doesn't block others).

        Returns:
            int: Number of jobs processed
        """
        pending_jobs = self.search([('state', '=', 'pending')], limit=10)

        if not pending_jobs:
            return 0

        _logger.info("JSOCR: Cron found %d pending job(s) to process", len(pending_jobs))

        processed = 0
        for job in pending_jobs:
            try:
                job._process_job_async()
                processed += 1
            except Exception as e:
                _logger.error(
                    "JSOCR: Cron failed to process job %s: %s",
                    job.id, type(e).__name__
                )
                # Continue with next job (NFR10)
                continue

        _logger.info("JSOCR: Cron processed %d job(s)", processed)
        return processed
