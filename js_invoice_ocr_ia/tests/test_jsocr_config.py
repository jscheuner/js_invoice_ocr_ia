# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

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
