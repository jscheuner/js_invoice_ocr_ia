# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import logging
import os
import re
import requests
from pathlib import Path
from odoo import models, fields, api, tools
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class JsocrConfig(models.Model):
    """Configuration singleton pour JSOCR Invoice OCR IA"""

    _name = 'jsocr.config'
    _description = 'JSOCR Invoice OCR IA Configuration'

    # Singleton marker field - ensures only one record can exist
    singleton_marker = fields.Char(
        string='Singleton Marker',
        default='singleton',
        readonly=True,
        copy=False,
    )

    # URL et modèle Ollama
    ollama_url = fields.Char(
        string='Ollama URL',
        default='http://localhost:11434',
        required=True,
        help='URL du serveur Ollama pour analyse IA (ex: http://localhost:11434)'
    )

    ollama_model = fields.Selection(
        selection='_get_ollama_models',
        string='Ollama Model',
        default='llama3',
        help='Nom du modèle IA à utiliser (ex: llama3, mistral)'
    )

    ollama_timeout = fields.Integer(
        string='Ollama Timeout',
        default=120,
        help='Timeout en secondes pour les requêtes Ollama (default: 120s)'
    )

    # Chemins des dossiers de traitement
    watch_folder_path = fields.Char(
        string='Watch Folder',
        default='/opt/odoo/ocr_input',
        required=True,
        help='Chemin du dossier à surveiller pour nouveaux PDFs'
    )

    success_folder_path = fields.Char(
        string='Success Folder',
        default='/opt/odoo/ocr_success',
        required=True,
        help='Chemin du dossier pour fichiers traités avec succès'
    )

    error_folder_path = fields.Char(
        string='Error Folder',
        default='/opt/odoo/ocr_error',
        required=True,
        help='Chemin du dossier pour fichiers en erreur'
    )

    rejected_folder_path = fields.Char(
        string='Rejected Folder',
        default='/opt/odoo/ocr_rejected',
        required=True,
        help='Chemin du dossier pour fichiers non-PDF rejetés'
    )

    # Alertes et notifications
    alert_amount_threshold = fields.Float(
        string='Alert Amount Threshold',
        default=10000.0,
        help='Seuil d'alerte pour montants élevés (en CHF)'
    )

    alert_email = fields.Char(
        string='Alert Email',
        help='Email pour notifications d\'erreur (optionnel)'
    )

    # Contrainte singleton: un seul enregistrement possible via champ constant
    _sql_constraints = [
        ('unique_singleton', 'unique(singleton_marker)', 'Only one configuration record is allowed!')
    ]

    @api.constrains('ollama_url')
    def _check_ollama_url(self):
        """Validate URL format for ollama_url"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        for record in self:
            if record.ollama_url and not url_pattern.match(record.ollama_url):
                raise ValidationError(
                    "L'URL Ollama n'est pas valide. Format attendu: http(s)://host:port"
                )

    @api.constrains('alert_email')
    def _check_alert_email(self):
        """Validate email format for alert_email"""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        for record in self:
            if record.alert_email and not email_pattern.match(record.alert_email):
                raise ValidationError(
                    "L'adresse email d'alerte n'est pas valide."
                )

    @api.constrains('watch_folder_path', 'success_folder_path', 'error_folder_path', 'rejected_folder_path')
    def _check_folder_paths(self):
        """Validate folder paths are absolute with existing, accessible parents"""
        for record in self:
            folder_fields = {
                'watch_folder_path': 'Dossier surveillé',
                'success_folder_path': 'Dossier succès',
                'error_folder_path': 'Dossier erreur',
                'rejected_folder_path': 'Dossier rejeté',
            }

            for field_name, field_label in folder_fields.items():
                path_str = getattr(record, field_name)
                if not path_str:
                    continue

                try:
                    path = Path(path_str)
                except (OSError, ValueError) as e:
                    raise ValidationError(
                        f"{field_label}: Chemin invalide - {path_str}. "
                        f"Erreur: {str(e)}"
                    )

                # Vérifier chemin absolu
                if not path.is_absolute():
                    raise ValidationError(
                        f"{field_label}: Le chemin doit être absolu. "
                        f"Valeur actuelle: {path_str}"
                    )

                # Vérifier existence du parent
                parent = path.parent
                if not parent.exists():
                    raise ValidationError(
                        f"{field_label}: Le répertoire parent n'existe pas. "
                        f"Parent attendu: {parent}"
                    )

                # Vérifier permissions
                if not os.access(str(parent), os.R_OK | os.W_OK):
                    raise ValidationError(
                        f"{field_label}: Permissions insuffisantes (lecture/écriture requises). "
                        f"Chemin: {path_str}"
                    )

    @api.model
    @tools.ormcache()
    def get_config(self):
        """Retourne l'enregistrement de configuration unique (le crée si nécessaire)

        Uses sudo() to ensure creation works even for users without create rights.
        Result is cached via @tools.ormcache for performance.

        Returns:
            jsocr.config: L'enregistrement de configuration unique
        """
        config = self.search([], limit=1)
        if not config:
            # Use sudo() to create config even if current user lacks create rights
            config = self.sudo().create({})
        return config

    def write(self, vals):
        """Clear cache when config is modified"""
        self.env.registry.clear_cache()
        return super().write(vals)

    def _get_ollama_models(self):
        """Retourne la liste des modèles disponibles pour le champ Selection.

        Called automatically by Odoo when rendering the Selection field.
        Fetches available models from Ollama API and formats them for the dropdown.

        Returns:
            list: Liste de tuples (value, label) pour le champ Selection.
                  Retourne au moins le modèle par défaut si aucun modèle disponible.
        """
        models = self._fetch_available_models()
        if not models:
            # Fallback: retourner au moins le modèle par défaut
            return [('llama3', 'llama3 (défaut)')]

        return [(model, model) for model in models]

    def _fetch_available_models(self):
        """Récupère les modèles disponibles depuis Ollama API.

        Calls GET /api/tags endpoint silently (no user errors raised).
        Used to populate the Selection field dropdown.

        Returns:
            list: Liste des noms de modèles, ou liste vide si erreur
        """
        if not self.ollama_url:
            return []

        try:
            response = requests.get(
                f"{self.ollama_url}/api/tags",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                _logger.info(f"JSOCR: Retrieved {len(models)} model(s) from Ollama")
                return models
        except Exception as e:
            _logger.warning(f"JSOCR: Could not fetch models - {type(e).__name__}")
            return []

        return []

    # Button action method - no decorator needed, called via type="object" in view
    def test_ollama_connection(self):
        """Test Ollama server connection and retrieve available models.

        Sends GET request to {ollama_url}/api/tags to verify connectivity
        and list available models. Results displayed via Odoo notification.

        Note: Uses 10s timeout (hardcoded) for connection test, while ollama_timeout
        field (120s default) is used for actual AI processing requests.

        Example:
            config = self.env['jsocr.config'].get_config()
            result = config.test_ollama_connection()
            # Returns notification dict or raises UserError

        Returns:
            dict: Client action for Odoo notification

        Raises:
            UserError: If connection fails or URL not configured
        """
        self.ensure_one()  # Singleton pattern

        if not self.ollama_url:
            raise UserError("L'URL Ollama n'est pas configurée")

        _logger.info("JSOCR: Testing Ollama connection")

        try:
            response = requests.get(
                f"{self.ollama_url}/api/tags",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]

                if models:
                    message = f"Connexion OK - Modèles disponibles: {', '.join(models)}"
                else:
                    message = "Connexion OK - Aucun modèle disponible"

                _logger.info(f"JSOCR: Ollama connection successful - {len(models)} model(s) found")

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Succès',
                        'message': message,
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                error_msg = f"Erreur de connexion: HTTP {response.status_code}"
                _logger.warning(f"JSOCR: Ollama connection failed - HTTP {response.status_code}")
                raise UserError(error_msg)

        except requests.Timeout:
            error_msg = "Erreur de connexion: Timeout après 10s"
            _logger.warning("JSOCR: Ollama connection timeout")
            raise UserError(error_msg)

        except requests.ConnectionError:
            error_msg = "Erreur de connexion au serveur Ollama"
            _logger.error("JSOCR: Ollama connection error")
            raise UserError(error_msg)

        except ValueError:
            error_msg = "Erreur: Réponse JSON invalide du serveur Ollama"
            _logger.error("JSOCR: Invalid JSON response from Ollama")
            raise UserError(error_msg)
        except KeyError:
            error_msg = "Erreur: Structure de réponse invalide du serveur Ollama"
            _logger.error("JSOCR: Invalid response structure from Ollama")
            raise UserError(error_msg)
