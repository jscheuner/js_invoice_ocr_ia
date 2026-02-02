# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import base64
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
        help='Raw text extracted from PDF via OCR',
    )

    ai_response = fields.Text(
        string='AI Response (JSON)',
        help='Raw JSON response from Ollama AI analysis',
    )

    confidence_data = fields.Text(
        string='Confidence Data (JSON)',
        help='Per-field confidence scores in JSON format',
    )

    error_message = fields.Text(
        string='Error Message',
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
        help='Link to the generated supplier invoice',
    )

    correction_ids = fields.One2many(
        comodel_name='jsocr.correction',
        inverse_name='import_job_id',
        string='Corrections',
        help='User corrections associated with this import job',
    )

    # Retry management
    retry_count = fields.Integer(
        string='Retry Count',
        default=0,
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
