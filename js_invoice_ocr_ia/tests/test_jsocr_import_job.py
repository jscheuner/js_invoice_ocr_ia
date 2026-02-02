# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import base64
from odoo.tests import TransactionCase
from odoo.exceptions import UserError


class TestJsocrImportJob(TransactionCase):
    """Tests for jsocr.import.job model (state machine).

    This test suite covers:
    - Job creation and default values
    - Valid state transitions (draft -> pending -> processing -> done/error/failed)
    - Invalid state transitions (raises UserError)
    - Retry management with max 3 attempts
    - Computed fields (can_retry, is_final_state, next_retry_delay)
    - Helper methods (_should_retry, _get_retry_delay)
    """

    def setUp(self):
        super().setUp()
        self.Job = self.env['jsocr.import.job']
        # Fake PDF content encoded in base64
        self.fake_pdf = base64.b64encode(b'%PDF-1.4 fake content')

    def _create_job(self, **kwargs):
        """Create a job with default values for testing.

        Args:
            **kwargs: Override default field values.

        Returns:
            jsocr.import.job: Created job record.
        """
        vals = {
            'pdf_filename': 'test_invoice.pdf',
            'pdf_file': self.fake_pdf,
        }
        vals.update(kwargs)
        return self.Job.create(vals)

    # -------------------------------------------------------------------------
    # TEST: Creation et valeurs par defaut
    # -------------------------------------------------------------------------

    def test_create_job_default_state(self):
        """Test: un nouveau job est cree avec state='draft' et retry_count=0"""
        job = self._create_job()

        self.assertEqual(job.state, 'draft')
        self.assertEqual(job.retry_count, 0)
        self.assertFalse(job.error_message)
        self.assertFalse(job.invoice_id)

    def test_create_job_name_computed(self):
        """Test: le nom du job est auto-genere"""
        job = self._create_job(pdf_filename='facture_123.pdf')

        self.assertIn('facture_123.pdf', job.name)
        self.assertIn('Job #', job.name)

    def test_create_job_required_fields(self):
        """Test: pdf_file et pdf_filename sont requis"""
        with self.assertRaises(Exception):
            self.Job.create({})

    # -------------------------------------------------------------------------
    # TEST: Transitions d'etat valides
    # -------------------------------------------------------------------------

    def test_action_submit_draft_to_pending(self):
        """Test: action_submit() passe de draft a pending"""
        job = self._create_job()
        self.assertEqual(job.state, 'draft')

        job.action_submit()

        self.assertEqual(job.state, 'pending')

    def test_action_process_pending_to_processing(self):
        """Test: action_process() passe de pending a processing"""
        job = self._create_job()
        job.action_submit()
        self.assertEqual(job.state, 'pending')

        job.action_process()

        self.assertEqual(job.state, 'processing')

    def test_action_mark_done_processing_to_done(self):
        """Test: action_mark_done() passe de processing a done"""
        job = self._create_job()
        job.action_submit()
        job.action_process()
        self.assertEqual(job.state, 'processing')

        job.action_mark_done()

        self.assertEqual(job.state, 'done')

    def test_action_mark_error_processing_to_error(self):
        """Test: action_mark_error() passe de processing a error"""
        job = self._create_job()
        job.action_submit()
        job.action_process()

        job.action_mark_error('Connection timeout')

        self.assertEqual(job.state, 'error')
        self.assertEqual(job.error_message, 'Connection timeout')

    def test_action_retry_error_to_pending(self):
        """Test: action_retry() passe de error a pending et incremente retry_count"""
        job = self._create_job()
        job.action_submit()
        job.action_process()
        job.action_mark_error('Temporary error')
        self.assertEqual(job.state, 'error')
        self.assertEqual(job.retry_count, 0)

        job.action_retry()

        self.assertEqual(job.state, 'pending')
        self.assertEqual(job.retry_count, 1)
        self.assertFalse(job.error_message)

    def test_action_mark_failed_error_to_failed(self):
        """Test: action_mark_failed() passe de error a failed"""
        job = self._create_job()
        job.action_submit()
        job.action_process()
        job.action_mark_error('Fatal error')

        job.action_mark_failed()

        self.assertEqual(job.state, 'failed')

    def test_action_cancel_resets_to_draft(self):
        """Test: action_cancel() remet le job en draft"""
        job = self._create_job()
        job.action_submit()
        self.assertEqual(job.state, 'pending')

        job.action_cancel()

        self.assertEqual(job.state, 'draft')
        self.assertEqual(job.retry_count, 0)

    # -------------------------------------------------------------------------
    # TEST: Transitions d'etat invalides
    # -------------------------------------------------------------------------

    def test_cannot_submit_non_draft_job(self):
        """Test: on ne peut pas soumettre un job qui n'est pas en draft"""
        job = self._create_job()
        job.action_submit()  # now pending

        with self.assertRaises(UserError):
            job.action_submit()

    def test_cannot_process_non_pending_job(self):
        """Test: on ne peut pas processer un job qui n'est pas en pending"""
        job = self._create_job()  # draft

        with self.assertRaises(UserError):
            job.action_process()

    def test_cannot_mark_done_non_processing_job(self):
        """Test: on ne peut pas marquer done un job qui n'est pas en processing"""
        job = self._create_job()
        job.action_submit()  # pending

        with self.assertRaises(UserError):
            job.action_mark_done()

    def test_cannot_mark_error_non_processing_job(self):
        """Test: on ne peut pas marquer error un job qui n'est pas en processing"""
        job = self._create_job()

        with self.assertRaises(UserError):
            job.action_mark_error('Error')

    def test_cannot_retry_non_error_job(self):
        """Test: on ne peut pas retry un job qui n'est pas en error"""
        job = self._create_job()
        job.action_submit()

        with self.assertRaises(UserError):
            job.action_retry()

    def test_cannot_mark_failed_non_error_job(self):
        """Test: on ne peut pas marquer failed un job qui n'est pas en error"""
        job = self._create_job()

        with self.assertRaises(UserError):
            job.action_mark_failed()

    def test_cannot_cancel_done_job(self):
        """Test: on ne peut pas annuler un job en etat final done"""
        job = self._create_job()
        job.action_submit()
        job.action_process()
        job.action_mark_done()

        with self.assertRaises(UserError):
            job.action_cancel()

    def test_cannot_cancel_failed_job(self):
        """Test: on ne peut pas annuler un job en etat final failed"""
        job = self._create_job()
        job.action_submit()
        job.action_process()
        job.action_mark_error('Error')
        job.action_mark_failed()

        with self.assertRaises(UserError):
            job.action_cancel()

    # -------------------------------------------------------------------------
    # TEST: Gestion des retry
    # -------------------------------------------------------------------------

    def test_retry_increments_counter(self):
        """Test: chaque retry incremente le compteur"""
        job = self._create_job()
        job.action_submit()
        job.action_process()
        job.action_mark_error('Error 1')

        self.assertEqual(job.retry_count, 0)
        job.action_retry()
        self.assertEqual(job.retry_count, 1)

        job.action_process()
        job.action_mark_error('Error 2')
        job.action_retry()
        self.assertEqual(job.retry_count, 2)

        job.action_process()
        job.action_mark_error('Error 3')
        job.action_retry()
        self.assertEqual(job.retry_count, 3)

    def test_retry_max_attempts_reached(self):
        """Test: apres 3 tentatives, retry est refuse"""
        job = self._create_job()
        job.write({'state': 'error', 'retry_count': 3})

        with self.assertRaises(UserError) as ctx:
            job.action_retry()

        self.assertIn('Maximum retry attempts', str(ctx.exception))

    def test_can_retry_with_count_under_limit(self):
        """Test: retry possible si count < 3"""
        job = self._create_job()
        job.write({'state': 'error', 'retry_count': 2})

        # Should not raise
        job.action_retry()

        self.assertEqual(job.state, 'pending')
        self.assertEqual(job.retry_count, 3)

    # -------------------------------------------------------------------------
    # TEST: Champs calcules
    # -------------------------------------------------------------------------

    def test_can_retry_computed_true(self):
        """Test: can_retry est True si state=error et retry_count < 3"""
        job = self._create_job()
        job.write({'state': 'error', 'retry_count': 0})

        self.assertTrue(job.can_retry)

        job.retry_count = 2
        self.assertTrue(job.can_retry)

    def test_can_retry_computed_false_wrong_state(self):
        """Test: can_retry est False si state != error"""
        job = self._create_job()

        self.assertEqual(job.state, 'draft')
        self.assertFalse(job.can_retry)

    def test_can_retry_computed_false_max_retries(self):
        """Test: can_retry est False si retry_count >= 3"""
        job = self._create_job()
        job.write({'state': 'error', 'retry_count': 3})

        self.assertFalse(job.can_retry)

    def test_is_final_state_done(self):
        """Test: is_final_state est True si state=done"""
        job = self._create_job()
        job.action_submit()
        job.action_process()
        job.action_mark_done()

        self.assertTrue(job.is_final_state)

    def test_is_final_state_failed(self):
        """Test: is_final_state est True si state=failed"""
        job = self._create_job()
        job.write({'state': 'error'})
        job.action_mark_failed()

        self.assertTrue(job.is_final_state)

    def test_is_final_state_false_for_other_states(self):
        """Test: is_final_state est False pour draft, pending, processing, error"""
        job = self._create_job()

        self.assertEqual(job.state, 'draft')
        self.assertFalse(job.is_final_state)

        job.action_submit()
        self.assertEqual(job.state, 'pending')
        self.assertFalse(job.is_final_state)

        job.action_process()
        self.assertEqual(job.state, 'processing')
        self.assertFalse(job.is_final_state)

        job.action_mark_error('Error')
        self.assertEqual(job.state, 'error')
        self.assertFalse(job.is_final_state)

    # -------------------------------------------------------------------------
    # TEST: Helper methods
    # -------------------------------------------------------------------------

    def test_should_retry_true_for_retryable_error(self):
        """Test: _should_retry retourne True pour erreurs recouvrables"""
        job = self._create_job()
        job.write({'state': 'error', 'retry_count': 0})

        self.assertTrue(job._should_retry('timeout'))
        self.assertTrue(job._should_retry('connection_error'))
        self.assertTrue(job._should_retry('service_unavailable'))

    def test_should_retry_false_for_non_retryable_error(self):
        """Test: _should_retry retourne False pour erreurs non recouvrables"""
        job = self._create_job()
        job.write({'state': 'error', 'retry_count': 0})

        self.assertFalse(job._should_retry('invalid_pdf'))
        self.assertFalse(job._should_retry('parsing_error'))

    def test_should_retry_false_when_max_attempts(self):
        """Test: _should_retry retourne False si retry_count >= 3"""
        job = self._create_job()
        job.write({'state': 'error', 'retry_count': 3})

        self.assertFalse(job._should_retry('timeout'))

    def test_get_retry_delay_first_attempt(self):
        """Test: _get_retry_delay returns 5s for first retry"""
        job = self._create_job()
        job.retry_count = 0

        self.assertEqual(job._get_retry_delay(), 5)

    def test_get_retry_delay_second_attempt(self):
        """Test: _get_retry_delay returns 15s for second retry"""
        job = self._create_job()
        job.retry_count = 1

        self.assertEqual(job._get_retry_delay(), 15)

    def test_get_retry_delay_third_attempt(self):
        """Test: _get_retry_delay returns 30s for third retry"""
        job = self._create_job()
        job.retry_count = 2

        self.assertEqual(job._get_retry_delay(), 30)

    def test_get_retry_delay_beyond_max(self):
        """Test: _get_retry_delay returns last delay (30s) when count exceeds delays"""
        job = self._create_job()
        job.retry_count = 5

        self.assertEqual(job._get_retry_delay(), 30)

    def test_next_retry_delay_computed(self):
        """Test: next_retry_delay computed field follows backoff pattern"""
        job = self._create_job()

        job.retry_count = 0
        self.assertEqual(job.next_retry_delay, 5)

        job.retry_count = 1
        self.assertEqual(job.next_retry_delay, 15)

        job.retry_count = 2
        self.assertEqual(job.next_retry_delay, 30)

    def test_action_mark_error_with_error_type(self):
        """Test: action_mark_error logs error_type parameter"""
        job = self._create_job()
        job.action_submit()
        job.action_process()

        # Should not raise, error_type is for logging
        job.action_mark_error('Connection failed', error_type='connection_error')

        self.assertEqual(job.state, 'error')
        self.assertEqual(job.error_message, 'Connection failed')

    def test_action_mark_error_default_message(self):
        """Test: action_mark_error uses default message if none provided"""
        job = self._create_job()
        job.action_submit()
        job.action_process()

        job.action_mark_error()

        self.assertEqual(job.error_message, 'Unknown error occurred')

    def test_action_cancel_resets_error_message(self):
        """Test: action_cancel clears error_message"""
        job = self._create_job()
        job.action_submit()
        job.action_process()
        job.action_mark_error('Some error')
        self.assertEqual(job.error_message, 'Some error')

        # Go back to pending via retry then cancel
        job.action_retry()
        job.action_cancel()

        self.assertFalse(job.error_message)

    def test_full_success_workflow(self):
        """Test: complete success workflow draft->pending->processing->done"""
        job = self._create_job(pdf_filename='invoice_success.pdf')

        self.assertEqual(job.state, 'draft')
        self.assertFalse(job.is_final_state)

        job.action_submit()
        self.assertEqual(job.state, 'pending')

        job.action_process()
        self.assertEqual(job.state, 'processing')

        job.action_mark_done()
        self.assertEqual(job.state, 'done')
        self.assertTrue(job.is_final_state)

    def test_full_failure_workflow_after_retries(self):
        """Test: failure workflow with max retries exhausted"""
        job = self._create_job(pdf_filename='invoice_fail.pdf')

        # First attempt
        job.action_submit()
        job.action_process()
        job.action_mark_error('Error 1', error_type='timeout')
        self.assertTrue(job.can_retry)
        job.action_retry()

        # Second attempt
        job.action_process()
        job.action_mark_error('Error 2', error_type='timeout')
        self.assertTrue(job.can_retry)
        job.action_retry()

        # Third attempt
        job.action_process()
        job.action_mark_error('Error 3', error_type='timeout')
        self.assertTrue(job.can_retry)
        job.action_retry()

        # Fourth attempt fails
        job.action_process()
        job.action_mark_error('Error 4', error_type='timeout')
        self.assertFalse(job.can_retry)  # retry_count is now 3

        # Must mark as failed
        job.action_mark_failed()
        self.assertEqual(job.state, 'failed')
        self.assertTrue(job.is_final_state)

    # -------------------------------------------------------------------------
    # TEST: OCR Text Extraction Integration (Story 3.1)
    # -------------------------------------------------------------------------

    def test_extract_text_missing_pdf(self):
        """Test: _extract_text raises error when PDF is missing"""
        job = self._create_job()
        job.pdf_file = False

        with self.assertRaises(UserError) as ctx:
            job._extract_text()

        self.assertIn('PDF file is missing', str(ctx.exception))

    def test_extract_text_invalid_pdf(self):
        """Test: _extract_text raises error for invalid PDF"""
        # Create job with invalid PDF content
        job = self._create_job()
        job.pdf_file = base64.b64encode(b'This is not a PDF')

        with self.assertRaises(UserError) as ctx:
            job._extract_text()

        self.assertIn('extraction failed', str(ctx.exception).lower())

    # -------------------------------------------------------------------------
    # TEST: Language Detection Field (Story 3.3)
    # -------------------------------------------------------------------------

    def test_detected_language_default_value(self):
        """Test: detected_language defaults to 'fr'"""
        job = self._create_job()

        self.assertEqual(job.detected_language, 'fr')

    def test_detected_language_field_exists(self):
        """Test: detected_language field is a Selection with valid values"""
        job = self._create_job()

        # Field should exist and have valid selection values
        field = self.Job._fields.get('detected_language')
        self.assertIsNotNone(field)
        self.assertEqual(field.type, 'selection')

        # Check allowed values
        selection_values = [v[0] for v in field.selection]
        self.assertIn('fr', selection_values)
        self.assertIn('de', selection_values)
        self.assertIn('en', selection_values)

    # -------------------------------------------------------------------------
    # TEST: PDF File Movement to Success Folder (Story 3.6)
    # -------------------------------------------------------------------------

    def test_pdf_moved_to_success_on_done(self):
        """Test: PDF is moved to success folder when job is marked done"""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            success_path = os.path.join(temp_dir, 'success')
            os.makedirs(success_path)

            # Configure success folder
            config = self.env['jsocr.config'].get_config()
            config.write({'success_folder_path': success_path})

            # Create and process job
            job = self._create_job(pdf_filename='invoice_test.pdf')
            job.action_submit()
            job.action_process()
            job.action_mark_done()

            # Check file exists in success folder
            files = os.listdir(success_path)
            self.assertEqual(len(files), 1)
            self.assertIn('invoice_test.pdf', files[0])

    def test_success_filename_has_timestamp(self):
        """Test: success filename has timestamp prefix YYYYMMDD_HHMMSS_"""
        import os
        import re
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            success_path = os.path.join(temp_dir, 'success')
            os.makedirs(success_path)

            config = self.env['jsocr.config'].get_config()
            config.write({'success_folder_path': success_path})

            job = self._create_job(pdf_filename='facture.pdf')
            job.action_submit()
            job.action_process()
            job.action_mark_done()

            files = os.listdir(success_path)
            self.assertEqual(len(files), 1)

            # Verify timestamp format: YYYYMMDD_HHMMSS_facture.pdf
            filename = files[0]
            self.assertRegex(filename, r'^\d{8}_\d{6}_facture\.pdf$')

    def test_success_file_content_preserved(self):
        """Test: PDF content is preserved in success folder"""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            success_path = os.path.join(temp_dir, 'success')
            os.makedirs(success_path)

            config = self.env['jsocr.config'].get_config()
            config.write({'success_folder_path': success_path})

            # Create job with known content
            pdf_content = b'%PDF-1.4 test content for verification'
            job = self._create_job(
                pdf_filename='content_test.pdf',
                pdf_file=base64.b64encode(pdf_content)
            )
            job.action_submit()
            job.action_process()
            job.action_mark_done()

            # Read file content from success folder
            files = os.listdir(success_path)
            with open(os.path.join(success_path, files[0]), 'rb') as f:
                saved_content = f.read()

            self.assertEqual(saved_content, pdf_content)

    # -------------------------------------------------------------------------
    # TEST: PDF File Movement to Error Folder (Story 3.7)
    # -------------------------------------------------------------------------

    def test_pdf_moved_to_error_on_failed(self):
        """Test: PDF is moved to error folder when job is marked failed"""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            error_path = os.path.join(temp_dir, 'error')
            os.makedirs(error_path)

            config = self.env['jsocr.config'].get_config()
            config.write({
                'error_folder_path': error_path,
                'alert_email': False,
            })

            job = self._create_job(pdf_filename='failed_invoice.pdf')
            job.action_submit()
            job.action_process()
            job.action_mark_error('Processing failed')
            job.action_mark_failed()

            files = os.listdir(error_path)
            self.assertEqual(len(files), 1)
            self.assertIn('failed_invoice.pdf', files[0])

    def test_error_filename_has_timestamp(self):
        """Test: error filename has timestamp prefix YYYYMMDD_HHMMSS_"""
        import os
        import re
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            error_path = os.path.join(temp_dir, 'error')
            os.makedirs(error_path)

            config = self.env['jsocr.config'].get_config()
            config.write({
                'error_folder_path': error_path,
                'alert_email': False,
            })

            job = self._create_job(pdf_filename='erreur.pdf')
            job.action_submit()
            job.action_process()
            job.action_mark_error('Error')
            job.action_mark_failed()

            files = os.listdir(error_path)
            self.assertEqual(len(files), 1)

            # Verify timestamp format
            filename = files[0]
            self.assertRegex(filename, r'^\d{8}_\d{6}_erreur\.pdf$')

    def test_failure_alert_email_sent(self):
        """Test: email alert sent when job is marked failed and alert_email configured"""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            error_path = os.path.join(temp_dir, 'error')
            os.makedirs(error_path)

            config = self.env['jsocr.config'].get_config()
            config.write({
                'error_folder_path': error_path,
                'alert_email': 'admin@example.com',
            })

            mails_before = self.env['mail.mail'].search_count([])

            job = self._create_job(pdf_filename='alert_test.pdf')
            job.action_submit()
            job.action_process()
            job.action_mark_error('Critical failure')
            job.action_mark_failed()

            mails_after = self.env['mail.mail'].search_count([])
            self.assertEqual(mails_after, mails_before + 1)

            mail = self.env['mail.mail'].search([], order='id desc', limit=1)
            self.assertEqual(mail.email_to, 'admin@example.com')
            self.assertIn('alert_test.pdf', mail.subject)
            self.assertIn('Critical failure', mail.body_html)

    def test_no_failure_email_if_not_configured(self):
        """Test: no email sent when alert_email is not configured"""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            error_path = os.path.join(temp_dir, 'error')
            os.makedirs(error_path)

            config = self.env['jsocr.config'].get_config()
            config.write({
                'error_folder_path': error_path,
                'alert_email': False,
            })

            mails_before = self.env['mail.mail'].search_count([])

            job = self._create_job(pdf_filename='no_alert.pdf')
            job.action_submit()
            job.action_process()
            job.action_mark_error('Some error')
            job.action_mark_failed()

            mails_after = self.env['mail.mail'].search_count([])
            self.assertEqual(mails_after, mails_before)
