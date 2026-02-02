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
