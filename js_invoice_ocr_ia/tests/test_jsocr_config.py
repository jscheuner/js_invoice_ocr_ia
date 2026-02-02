# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import os
from unittest.mock import patch, MagicMock, call
import requests
from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError, UserError
from psycopg2 import IntegrityError
import logging
from js_invoice_ocr_ia.models.jsocr_config import JsocrConfig


class TestJsocrConfig(TransactionCase):
    """Tests pour le modele jsocr.config (singleton de configuration)"""

    def setUp(self):
        super().setUp()
        self.JsocrConfig = self.env['jsocr.config']
        # Nettoyer tous les enregistrements existants
        self.JsocrConfig.search([]).unlink()
        # Clear cache after cleanup
        self.env.registry.clear_cache()

    def test_create_config(self):
        """Test: creation basique d'un enregistrement config"""
        config = self.JsocrConfig.create({
            'ollama_url': 'http://test:11434',
        })

        self.assertTrue(config)
        self.assertEqual(config.ollama_url, 'http://test:11434')

    def test_get_config_creates_if_missing(self):
        """Test: get_config cree un enregistrement si aucun n'existe"""
        # S'assurer qu'aucun enregistrement n'existe
        self.assertEqual(self.JsocrConfig.search_count([]), 0)

        # get_config doit creer un enregistrement
        config = self.JsocrConfig.get_config()

        self.assertTrue(config)
        self.assertEqual(self.JsocrConfig.search_count([]), 1)

    def test_get_config_returns_existing(self):
        """Test: get_config retourne l'enregistrement existant sans en creer un nouveau"""
        # Creer un enregistrement
        existing_config = self.JsocrConfig.create({'ollama_url': 'http://existing:11434'})
        # Clear cache to ensure fresh lookup
        self.env.registry.clear_cache()

        # get_config doit retourner le meme
        config = self.JsocrConfig.get_config()

        self.assertEqual(config.id, existing_config.id)
        self.assertEqual(config.ollama_url, 'http://existing:11434')
        # Verifier qu'il n'y a toujours qu'un seul enregistrement
        self.assertEqual(self.JsocrConfig.search_count([]), 1)

    def test_singleton_constraint_prevents_duplicate(self):
        """Test: contrainte SQL empeche la creation de plusieurs enregistrements"""
        # Creer le premier enregistrement
        self.JsocrConfig.create({'ollama_url': 'http://first:11434'})

        # Tenter de creer un deuxieme enregistrement devrait echouer
        # car la contrainte unique(singleton_marker) l'empeche
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.JsocrConfig.create({'ollama_url': 'http://second:11434'})

    def test_default_values(self):
        """Test: verifier toutes les valeurs par defaut"""
        config = self.JsocrConfig.create({})

        self.assertEqual(config.ollama_url, 'http://localhost:11434')
        self.assertEqual(config.ollama_model, 'llama3')
        self.assertEqual(config.ollama_timeout, 120)
        self.assertEqual(config.watch_folder_path, '/opt/jsocr/watch')
        self.assertEqual(config.success_folder_path, '/opt/jsocr/success')
        self.assertEqual(config.error_folder_path, '/opt/jsocr/error')
        self.assertEqual(config.rejected_folder_path, '/opt/jsocr/rejected')
        self.assertEqual(config.alert_amount_threshold, 10000.0)
        self.assertFalse(config.alert_email)
        self.assertEqual(config.singleton_marker, 'singleton')

    def test_ollama_timeout_field_exists(self):
        """Test: champ ollama_timeout existe avec valeur par defaut 120"""
        config = self.JsocrConfig.create({})
        self.assertEqual(config.ollama_timeout, 120)

        # Verify it can be modified
        config.write({'ollama_timeout': 60})
        self.assertEqual(config.ollama_timeout, 60)

    def test_all_fields_exist(self):
        """Test: tous les champs requis sont accessibles"""
        config = self.JsocrConfig.create({})

        # Verifier que tous les champs existent et sont accessibles
        self.assertIsNotNone(config.ollama_url)
        self.assertIsNotNone(config.ollama_model)
        self.assertIsNotNone(config.ollama_timeout)
        self.assertIsNotNone(config.watch_folder_path)
        self.assertIsNotNone(config.success_folder_path)
        self.assertIsNotNone(config.error_folder_path)
        self.assertIsNotNone(config.rejected_folder_path)
        self.assertIsNotNone(config.alert_amount_threshold)
        self.assertIsNotNone(config.singleton_marker)
        # alert_email peut etre False/None (optionnel)

    def test_all_fields_modifiable(self):
        """Test: tous les champs peuvent etre modifies"""
        config = self.JsocrConfig.create({})

        config.write({
            'ollama_url': 'http://modified:11434',
            'ollama_model': 'mistral',
            'ollama_timeout': 60,
            'watch_folder_path': '/custom/watch',
            'success_folder_path': '/custom/success',
            'error_folder_path': '/custom/error',
            'rejected_folder_path': '/custom/rejected',
            'alert_amount_threshold': 10000.0,
            'alert_email': 'test@example.com',
        })

        self.assertEqual(config.ollama_url, 'http://modified:11434')
        self.assertEqual(config.ollama_model, 'mistral')
        self.assertEqual(config.ollama_timeout, 60)
        self.assertEqual(config.watch_folder_path, '/custom/watch')
        self.assertEqual(config.success_folder_path, '/custom/success')
        self.assertEqual(config.error_folder_path, '/custom/error')
        self.assertEqual(config.rejected_folder_path, '/custom/rejected')
        self.assertEqual(config.alert_amount_threshold, 10000.0)
        self.assertEqual(config.alert_email, 'test@example.com')

    def test_invalid_ollama_url_raises_error(self):
        """Test: URL Ollama invalide leve une ValidationError"""
        with self.assertRaises(ValidationError):
            self.JsocrConfig.create({
                'ollama_url': 'not-a-valid-url',
            })

    def test_valid_ollama_urls(self):
        """Test: differents formats d'URL valides sont acceptes"""
        valid_urls = [
            'http://localhost:11434',
            'https://localhost:11434',
            'http://192.168.1.100:11434',
            'http://ollama.example.com:11434',
            'https://ollama.example.com',
        ]
        for url in valid_urls:
            # Clean up first
            self.JsocrConfig.search([]).unlink()
            self.env.registry.clear_cache()

            config = self.JsocrConfig.create({'ollama_url': url})
            self.assertEqual(config.ollama_url, url)

    def test_invalid_email_raises_error(self):
        """Test: email invalide leve une ValidationError"""
        config = self.JsocrConfig.create({})

        with self.assertRaises(ValidationError):
            config.write({'alert_email': 'not-an-email'})

    def test_valid_email_accepted(self):
        """Test: email valide est accepte"""
        config = self.JsocrConfig.create({})
        config.write({'alert_email': 'admin@example.com'})
        self.assertEqual(config.alert_email, 'admin@example.com')

    def test_empty_email_accepted(self):
        """Test: email vide/null est accepte (champ optionnel)"""
        config = self.JsocrConfig.create({'alert_email': ''})
        self.assertFalse(config.alert_email)

        config.write({'alert_email': False})
        self.assertFalse(config.alert_email)

    # -------------------------------------------------------------------------
    # Tests Ollama Connection (Story 2.3)
    # -------------------------------------------------------------------------

    @patch('js_invoice_ocr_ia.models.jsocr_config.requests.get')
    @patch('js_invoice_ocr_ia.models.jsocr_config._logger')
    def test_ollama_connection_success_with_models(self, mock_logger, mock_get):
        """Test: connexion reussie retourne les modeles disponibles"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [
                {'name': 'llama3:latest'},
                {'name': 'mistral:latest'}
            ]
        }
        mock_get.return_value = mock_response

        config = self.JsocrConfig.create({
            'ollama_url': 'http://localhost:11434'
        })

        result = config.test_ollama_connection()

        # Verifier que la notification contient les modeles
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertIn('llama3', result['params']['message'])
        self.assertIn('mistral', result['params']['message'])
        self.assertEqual(result['params']['type'], 'success')

        # Verifier que le timeout est de 10s
        mock_get.assert_called_once_with(
            'http://localhost:11434/api/tags',
            timeout=10
        )

        # Verifier que le logging a ete appele correctement
        mock_logger.info.assert_any_call("JSOCR: Testing Ollama connection")
        mock_logger.info.assert_any_call("JSOCR: Ollama connection successful - 2 model(s) found")

    @patch('js_invoice_ocr_ia.models.jsocr_config.requests.get')
    def test_ollama_connection_success_no_models(self, mock_get):
        """Test: connexion reussie sans modeles affiche message approprie"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'models': []}
        mock_get.return_value = mock_response

        config = self.JsocrConfig.create({
            'ollama_url': 'http://localhost:11434'
        })

        result = config.test_ollama_connection()

        self.assertIn('Aucun modele disponible', result['params']['message'])
        self.assertEqual(result['params']['type'], 'success')

    @patch('js_invoice_ocr_ia.models.jsocr_config.requests.get')
    @patch('js_invoice_ocr_ia.models.jsocr_config._logger')
    def test_ollama_connection_timeout(self, mock_logger, mock_get):
        """Test: timeout apres 10s leve UserError avec message approprie"""
        mock_get.side_effect = requests.Timeout()

        config = self.JsocrConfig.create({
            'ollama_url': 'http://localhost:11434'
        })

        with self.assertRaises(UserError) as cm:
            config.test_ollama_connection()

        self.assertIn('Timeout apres 10s', str(cm.exception))

        # Verifier que le logging a ete appele
        mock_logger.info.assert_called_once_with("JSOCR: Testing Ollama connection")
        mock_logger.warning.assert_called_once_with("JSOCR: Ollama connection timeout")

    @patch('js_invoice_ocr_ia.models.jsocr_config.requests.get')
    def test_ollama_connection_error(self, mock_get):
        """Test: erreur de connexion leve UserError"""
        mock_get.side_effect = requests.ConnectionError("Connection refused")

        config = self.JsocrConfig.create({
            'ollama_url': 'http://localhost:11434'
        })

        with self.assertRaises(UserError) as cm:
            config.test_ollama_connection()

        self.assertIn('Erreur de connexion au serveur Ollama', str(cm.exception))

    @patch('js_invoice_ocr_ia.models.jsocr_config.requests.get')
    def test_ollama_connection_http_error(self, mock_get):
        """Test: HTTP != 200 leve UserError avec status code"""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response

        config = self.JsocrConfig.create({
            'ollama_url': 'http://localhost:11434'
        })

        with self.assertRaises(UserError) as cm:
            config.test_ollama_connection()

        self.assertIn('HTTP 503', str(cm.exception))

    def test_ollama_connection_no_url(self):
        """Test: URL vide leve UserError"""
        config = self.JsocrConfig.create({
            'ollama_url': False  # Empty
        })

        with self.assertRaises(UserError) as cm:
            config.test_ollama_connection()

        self.assertIn('URL Ollama n\'est pas configuree', str(cm.exception))

    @patch('js_invoice_ocr_ia.models.jsocr_config.requests.get')
    def test_ollama_connection_invalid_json(self, mock_get):
        """Test: reponse JSON invalide geree gracieusement"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        config = self.JsocrConfig.create({
            'ollama_url': 'http://localhost:11434'
        })

        with self.assertRaises(UserError) as cm:
            config.test_ollama_connection()

        self.assertIn('JSON invalide', str(cm.exception))

    def test_ollama_connection_ensure_one_violation(self):
        """Test: ensure_one() leve ValueError sur recordset vide/multiple"""
        # Test avec recordset vide
        empty_recordset = self.JsocrConfig.browse([])
        with self.assertRaises(ValueError):
            empty_recordset.test_ollama_connection()

        # Test avec recordset multiple (creer 2 configs necessite contournement contrainte)
        # On ne peut pas vraiment tester multiple records a cause de la contrainte singleton
        # Mais on verifie au moins le comportement avec empty recordset

    @patch('odoo.models.Registry.clear_cache')
    def test_write_clears_cache(self, mock_clear_cache):
        """Test: write() appelle registry.clear_cache()"""
        config = self.JsocrConfig.create({
            'ollama_url': 'http://localhost:11434'
        })

        # Reset mock pour ignorer les appels precedents (create, etc.)
        mock_clear_cache.reset_mock()

        # Modifier la config
        config.write({'ollama_model': 'mistral'})

        # Verifier que clear_cache a ete appele
        mock_clear_cache.assert_called()

    # -------------------------------------------------------------------------
    # Tests Model Selection (Story 2.4)
    # -------------------------------------------------------------------------

    @patch('js_invoice_ocr_ia.models.jsocr_config.requests.get')
    def test_fetch_available_models_success(self, mock_get):
        """Test: _fetch_available_models retourne liste si connexion OK"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [
                {'name': 'llama3:latest'},
                {'name': 'mistral:latest'}
            ]
        }
        mock_get.return_value = mock_response

        config = self.JsocrConfig.create({
            'ollama_url': 'http://localhost:11434'
        })

        models = config._fetch_available_models()

        self.assertEqual(len(models), 2)
        self.assertIn('llama3:latest', models)
        self.assertIn('mistral:latest', models)

    @patch('js_invoice_ocr_ia.models.jsocr_config.requests.get')
    def test_fetch_available_models_connection_error(self, mock_get):
        """Test: _fetch_available_models retourne [] si erreur connexion"""
        mock_get.side_effect = requests.ConnectionError()

        config = self.JsocrConfig.create({
            'ollama_url': 'http://localhost:11434'
        })

        models = config._fetch_available_models()

        self.assertEqual(models, [])

    def test_fetch_available_models_no_url(self):
        """Test: _fetch_available_models retourne [] si pas d'URL"""
        config = self.JsocrConfig.create({
            'ollama_url': False
        })

        models = config._fetch_available_models()

        self.assertEqual(models, [])

    @patch('js_invoice_ocr_ia.models.jsocr_config.requests.get')
    def test_fetch_available_models_http_error(self, mock_get):
        """Test: _fetch_available_models retourne [] si HTTP != 200"""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response

        config = self.JsocrConfig.create({
            'ollama_url': 'http://localhost:11434'
        })

        models = config._fetch_available_models()

        self.assertEqual(models, [])

    @patch('js_invoice_ocr_ia.models.jsocr_config.requests.get')
    def test_fetch_available_models_timeout(self, mock_get):
        """Test: _fetch_available_models retourne [] si timeout"""
        mock_get.side_effect = requests.Timeout()

        config = self.JsocrConfig.create({
            'ollama_url': 'http://localhost:11434'
        })

        models = config._fetch_available_models()

        self.assertEqual(models, [])

    @patch.object(JsocrConfig, '_fetch_available_models')
    def test_get_ollama_models_with_data(self, mock_fetch):
        """Test: _get_ollama_models retourne tuples corrects"""
        mock_fetch.return_value = ['llama3:latest', 'mistral:latest']

        config = self.JsocrConfig.create({})

        selection = config._get_ollama_models()

        self.assertIsInstance(selection, list)
        self.assertEqual(len(selection), 2)
        self.assertEqual(selection[0], ('llama3:latest', 'llama3:latest'))
        self.assertEqual(selection[1], ('mistral:latest', 'mistral:latest'))

    @patch.object(JsocrConfig, '_fetch_available_models')
    def test_get_ollama_models_fallback(self, mock_fetch):
        """Test: _get_ollama_models retourne defaut si liste vide"""
        mock_fetch.return_value = []

        config = self.JsocrConfig.create({})

        selection = config._get_ollama_models()

        self.assertEqual(len(selection), 1)
        self.assertEqual(selection[0][0], 'llama3')
        self.assertIn('defaut', selection[0][1])

    def test_ollama_model_field_is_selection(self):
        """Test: champ ollama_model est de type Selection"""
        config = self.JsocrConfig.create({})

        # Verifier que le champ existe et est modifiable
        config.write({'ollama_model': 'llama3'})
        self.assertEqual(config.ollama_model, 'llama3')

        config.write({'ollama_model': 'mistral'})
        self.assertEqual(config.ollama_model, 'mistral')

    def test_ollama_model_default_value(self):
        """Test: valeur par defaut 'llama3' est preservee"""
        config = self.JsocrConfig.create({})

        self.assertEqual(config.ollama_model, 'llama3')

    # -------------------------------------------------------------------------
    # Tests supplementaires Story 2.4 (Corrections post-review)
    # -------------------------------------------------------------------------

    @patch('js_invoice_ocr_ia.models.jsocr_config.requests.get')
    def test_fetch_available_models_invalid_json(self, mock_get):
        """Test: _fetch_available_models retourne [] si JSON invalide"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        config = self.JsocrConfig.create({
            'ollama_url': 'http://localhost:11434'
        })

        models = config._fetch_available_models()

        self.assertEqual(models, [])

    @patch('js_invoice_ocr_ia.models.jsocr_config.requests.get')
    @patch('js_invoice_ocr_ia.models.jsocr_config._logger')
    def test_fetch_available_models_logs_success(self, mock_logger, mock_get):
        """Test: _fetch_available_models log le nombre de modeles recuperes"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [
                {'name': 'llama3:latest'},
                {'name': 'mistral:latest'}
            ]
        }
        mock_get.return_value = mock_response

        config = self.JsocrConfig.create({
            'ollama_url': 'http://localhost:11434'
        })

        models = config._fetch_available_models()

        # Verifier le log de succes
        mock_logger.info.assert_called_once_with("JSOCR: Retrieved 2 model(s) from Ollama")

    @patch('js_invoice_ocr_ia.models.jsocr_config.requests.get')
    @patch('js_invoice_ocr_ia.models.jsocr_config._logger')
    def test_fetch_available_models_logs_error(self, mock_logger, mock_get):
        """Test: _fetch_available_models log les erreurs de connexion"""
        mock_get.side_effect = requests.ConnectionError()

        config = self.JsocrConfig.create({
            'ollama_url': 'http://localhost:11434'
        })

        models = config._fetch_available_models()

        # Verifier le log d'erreur
        mock_logger.warning.assert_called_once_with("JSOCR: Could not fetch models - ConnectionError")

    # ========================================
    # Tests pour Story 2.5: Configuration des Alertes
    # ========================================

    def test_alert_amount_threshold_accepts_positive_values(self):
        """Test: alert_amount_threshold accepte montants > 0"""
        config = self.JsocrConfig.create({
            'alert_amount_threshold': 5000.0
        })
        self.assertEqual(config.alert_amount_threshold, 5000.0)

        # Test avec d'autres valeurs positives
        config.write({'alert_amount_threshold': 1.0})
        self.assertEqual(config.alert_amount_threshold, 1.0)

        config.write({'alert_amount_threshold': 100000.0})
        self.assertEqual(config.alert_amount_threshold, 100000.0)

    def test_alert_amount_threshold_rejects_zero(self):
        """Test: alert_amount_threshold rejette 0"""
        with self.assertRaises(ValidationError) as context:
            self.JsocrConfig.create({
                'alert_amount_threshold': 0.0
            })
        self.assertIn("seuil d'alerte", str(context.exception).lower())

    def test_alert_amount_threshold_rejects_negative(self):
        """Test: alert_amount_threshold rejette valeurs negatives"""
        with self.assertRaises(ValidationError) as context:
            self.JsocrConfig.create({
                'alert_amount_threshold': -100.0
            })
        self.assertIn("seuil d'alerte", str(context.exception).lower())

        # Test avec write aussi
        config = self.JsocrConfig.create({'alert_amount_threshold': 5000.0})
        with self.assertRaises(ValidationError):
            config.write({'alert_amount_threshold': -50.0})

    def test_alert_email_accepts_valid_format(self):
        """Test: alert_email accepte format valide"""
        config = self.JsocrConfig.create({
            'alert_email': 'admin@example.com'
        })
        self.assertEqual(config.alert_email, 'admin@example.com')

        # Test avec d'autres formats valides
        config.write({'alert_email': 'test.user+tag@sub.domain.com'})
        self.assertEqual(config.alert_email, 'test.user+tag@sub.domain.com')

    def test_alert_email_rejects_invalid_format(self):
        """Test: alert_email rejette format invalide"""
        with self.assertRaises(ValidationError) as context:
            self.JsocrConfig.create({
                'alert_email': 'not-an-email'
            })
        self.assertIn("email", str(context.exception).lower())

        # Test avec d'autres formats invalides
        config = self.JsocrConfig.create({'alert_email': False})

        with self.assertRaises(ValidationError):
            config.write({'alert_email': 'missing@domain'})

        with self.assertRaises(ValidationError):
            config.write({'alert_email': '@nodomain.com'})

    def test_alert_email_accepts_empty_value(self):
        """Test: alert_email peut etre vide (optionnel)"""
        config = self.JsocrConfig.create({
            'alert_email': False
        })
        self.assertFalse(config.alert_email)

        # Test avec empty string aussi
        config.write({'alert_email': ''})
        self.assertFalse(config.alert_email)

    def test_alert_fields_default_values(self):
        """Test: valeurs par defaut correctes"""
        config = self.JsocrConfig.get_config()
        self.assertEqual(config.alert_amount_threshold, 10000.0)
        self.assertFalse(config.alert_email)

    # -------------------------------------------------------------------------
    # TEST: Folder Scanning (Story 3.4)
    # -------------------------------------------------------------------------

    def test_scan_input_folder_no_config(self):
        """Test: scan_input_folder returns 0 when watch folder not configured"""
        # Get config and clear watch folder
        config = self.JsocrConfig.get_config()
        config.write({'watch_folder_path': False})

        result = self.JsocrConfig.scan_input_folder()

        self.assertEqual(result, 0)

    def test_scan_input_folder_empty_folder(self):
        """Test: scan_input_folder returns 0 for empty folder"""
        import tempfile
        import os

        # Create a temporary empty directory
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.JsocrConfig.get_config()
            config.write({'watch_folder_path': temp_dir})

            result = self.JsocrConfig.scan_input_folder()

            self.assertEqual(result, 0)

    def test_scan_input_folder_with_pdf(self):
        """Test: scan_input_folder creates job for PDF file"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test PDF file (minimal valid PDF)
            pdf_path = os.path.join(temp_dir, 'test_invoice.pdf')
            # Minimal PDF content
            pdf_content = b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF'

            with open(pdf_path, 'wb') as f:
                f.write(pdf_content)

            config = self.JsocrConfig.get_config()
            config.write({'watch_folder_path': temp_dir})

            # Count jobs before
            jobs_before = self.env['jsocr.import.job'].search_count([])

            result = self.JsocrConfig.scan_input_folder()

            # Count jobs after
            jobs_after = self.env['jsocr.import.job'].search_count([])

            self.assertEqual(result, 1)
            self.assertEqual(jobs_after, jobs_before + 1)

            # Verify job was created correctly
            job = self.env['jsocr.import.job'].search([], order='id desc', limit=1)
            self.assertEqual(job.pdf_filename, 'test_invoice.pdf')
            self.assertEqual(job.state, 'pending')
            self.assertTrue(job.pdf_file)

            # Verify file was removed from watch folder
            self.assertFalse(os.path.exists(pdf_path))

    def test_scan_input_folder_ignores_non_pdf(self):
        """Test: scan_input_folder ignores non-PDF files"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create non-PDF files
            txt_path = os.path.join(temp_dir, 'document.txt')
            with open(txt_path, 'w') as f:
                f.write('This is a text file')

            doc_path = os.path.join(temp_dir, 'document.docx')
            with open(doc_path, 'wb') as f:
                f.write(b'fake docx content')

            config = self.JsocrConfig.get_config()
            config.write({'watch_folder_path': temp_dir})

            jobs_before = self.env['jsocr.import.job'].search_count([])

            result = self.JsocrConfig.scan_input_folder()

            jobs_after = self.env['jsocr.import.job'].search_count([])

            self.assertEqual(result, 0)
            self.assertEqual(jobs_after, jobs_before)

            # Files should still exist (not processed)
            self.assertTrue(os.path.exists(txt_path))
            self.assertTrue(os.path.exists(doc_path))

    def test_scan_input_folder_multiple_pdfs(self):
        """Test: scan_input_folder processes multiple PDF files"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_content = b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF'

            # Create 3 PDF files
            for i in range(3):
                pdf_path = os.path.join(temp_dir, f'invoice_{i}.pdf')
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_content)

            config = self.JsocrConfig.get_config()
            config.write({'watch_folder_path': temp_dir})

            jobs_before = self.env['jsocr.import.job'].search_count([])

            result = self.JsocrConfig.scan_input_folder()

            jobs_after = self.env['jsocr.import.job'].search_count([])

            self.assertEqual(result, 3)
            self.assertEqual(jobs_after, jobs_before + 3)

    def test_scan_input_folder_nonexistent_folder(self):
        """Test: scan_input_folder handles nonexistent folder gracefully"""
        config = self.JsocrConfig.get_config()
        config.write({'watch_folder_path': '/nonexistent/path/that/does/not/exist'})

        # Should not raise, just return 0
        result = self.JsocrConfig.scan_input_folder()

        self.assertEqual(result, 0)

    # -------------------------------------------------------------------------
    # TEST: Non-PDF File Rejection (Story 3.5)
    # -------------------------------------------------------------------------

    def test_non_pdf_detected_and_rejected(self):
        """Test: non-PDF file is moved to rejected folder"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            watch_path = os.path.join(temp_dir, 'watch')
            rejected_path = os.path.join(temp_dir, 'rejected')
            os.makedirs(watch_path)
            os.makedirs(rejected_path)

            # Create a non-PDF file in watch folder
            txt_path = os.path.join(watch_path, 'document.txt')
            with open(txt_path, 'w') as f:
                f.write('This is not a PDF')

            config = self.JsocrConfig.get_config()
            config.write({
                'watch_folder_path': watch_path,
                'rejected_folder_path': rejected_path,
                'alert_email': False,
            })

            self.JsocrConfig.scan_input_folder()

            # File should be removed from watch folder
            self.assertFalse(os.path.exists(txt_path))

            # File should exist in rejected folder
            rejected_file = os.path.join(rejected_path, 'document.txt')
            self.assertTrue(os.path.exists(rejected_file))

    def test_duplicate_filename_with_timestamp(self):
        """Test: duplicate filename gets timestamp prefix"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            watch_path = os.path.join(temp_dir, 'watch')
            rejected_path = os.path.join(temp_dir, 'rejected')
            os.makedirs(watch_path)
            os.makedirs(rejected_path)

            # Create a file already in rejected folder
            existing_file = os.path.join(rejected_path, 'document.txt')
            with open(existing_file, 'w') as f:
                f.write('Existing rejected file')

            # Create a file with same name in watch folder
            new_file = os.path.join(watch_path, 'document.txt')
            with open(new_file, 'w') as f:
                f.write('New file to reject')

            config = self.JsocrConfig.get_config()
            config.write({
                'watch_folder_path': watch_path,
                'rejected_folder_path': rejected_path,
                'alert_email': False,
            })

            self.JsocrConfig.scan_input_folder()

            # Original file should still exist
            self.assertTrue(os.path.exists(existing_file))

            # New file should be removed from watch
            self.assertFalse(os.path.exists(new_file))

            # Check that a timestamped file was created in rejected folder
            rejected_files = os.listdir(rejected_path)
            self.assertEqual(len(rejected_files), 2)

            # One of the files should have timestamp prefix (format: YYYYMMDD_HHMMSS_document.txt)
            timestamped_files = [f for f in rejected_files if '_document.txt' in f]
            self.assertEqual(len(timestamped_files), 1)

            # Verify timestamp format (YYYYMMDD_HHMMSS_)
            timestamped_name = timestamped_files[0]
            self.assertRegex(timestamped_name, r'^\d{8}_\d{6}_document\.txt$')

    @patch('js_invoice_ocr_ia.models.jsocr_config._logger')
    def test_alert_email_sent_on_rejection(self, mock_logger):
        """Test: email alert sent when non-PDF file is rejected"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            watch_path = os.path.join(temp_dir, 'watch')
            rejected_path = os.path.join(temp_dir, 'rejected')
            os.makedirs(watch_path)
            os.makedirs(rejected_path)

            # Create a non-PDF file
            txt_path = os.path.join(watch_path, 'malicious.exe')
            with open(txt_path, 'w') as f:
                f.write('fake executable')

            config = self.JsocrConfig.get_config()
            config.write({
                'watch_folder_path': watch_path,
                'rejected_folder_path': rejected_path,
                'alert_email': 'admin@example.com',
            })

            # Count mail records before
            mails_before = self.env['mail.mail'].search_count([])

            self.JsocrConfig.scan_input_folder()

            # Count mail records after
            mails_after = self.env['mail.mail'].search_count([])

            # A mail should have been created
            self.assertEqual(mails_after, mails_before + 1)

            # Check the mail content
            mail = self.env['mail.mail'].search([], order='id desc', limit=1)
            self.assertEqual(mail.email_to, 'admin@example.com')
            self.assertIn('JSOCR', mail.subject)
            self.assertIn('malicious.exe', mail.body_html)

    def test_no_email_if_not_configured(self):
        """Test: no email sent when alert_email is not configured"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            watch_path = os.path.join(temp_dir, 'watch')
            rejected_path = os.path.join(temp_dir, 'rejected')
            os.makedirs(watch_path)
            os.makedirs(rejected_path)

            # Create a non-PDF file
            txt_path = os.path.join(watch_path, 'document.txt')
            with open(txt_path, 'w') as f:
                f.write('text content')

            config = self.JsocrConfig.get_config()
            config.write({
                'watch_folder_path': watch_path,
                'rejected_folder_path': rejected_path,
                'alert_email': False,  # No email configured
            })

            # Count mail records before
            mails_before = self.env['mail.mail'].search_count([])

            self.JsocrConfig.scan_input_folder()

            # Count mail records after
            mails_after = self.env['mail.mail'].search_count([])

            # No mail should have been created
            self.assertEqual(mails_after, mails_before)

    @patch('js_invoice_ocr_ia.models.jsocr_config._logger')
    def test_rejection_logging(self, mock_logger):
        """Test: rejection is logged with JSOCR prefix"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            watch_path = os.path.join(temp_dir, 'watch')
            rejected_path = os.path.join(temp_dir, 'rejected')
            os.makedirs(watch_path)
            os.makedirs(rejected_path)

            # Create a non-PDF file
            txt_path = os.path.join(watch_path, 'report.docx')
            with open(txt_path, 'w') as f:
                f.write('docx content')

            config = self.JsocrConfig.get_config()
            config.write({
                'watch_folder_path': watch_path,
                'rejected_folder_path': rejected_path,
                'alert_email': False,
            })

            self.JsocrConfig.scan_input_folder()

            # Verify logging call with JSOCR prefix
            mock_logger.info.assert_any_call(
                "JSOCR: Rejected non-PDF file: %s", "report.docx"
            )
