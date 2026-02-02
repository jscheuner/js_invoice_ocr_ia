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

    # URL et modele Ollama
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
        help='Nom du modele IA a utiliser (ex: llama3, mistral)'
    )

    ollama_timeout = fields.Integer(
        string='Ollama Timeout',
        default=120,
        help='Timeout en secondes pour les requetes Ollama (default: 120s)'
    )

    # Chemins des dossiers de traitement
    watch_folder_path = fields.Char(
        string='Watch Folder',
        default='/opt/odoo/ocr_input',
        required=True,
        help='Chemin du dossier a surveiller pour nouveaux PDFs'
    )

    success_folder_path = fields.Char(
        string='Success Folder',
        default='/opt/odoo/ocr_success',
        required=True,
        help='Chemin du dossier pour fichiers traites avec succes'
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
        help='Chemin du dossier pour fichiers non-PDF rejetes'
    )

    # Alertes et notifications
    alert_amount_threshold = fields.Float(
        string='Alert Amount Threshold',
        default=10000.0,
        help='Seuil d\'alerte pour montants eleves (en CHF)'
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

    @api.constrains('alert_amount_threshold')
    def _check_alert_amount_threshold(self):
        """Validate that alert_amount_threshold is positive"""
        for record in self:
            if record.alert_amount_threshold is not None and record.alert_amount_threshold <= 0:
                raise ValidationError(
                    "Le seuil d'alerte doit etre un montant positif (> 0)."
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
                'watch_folder_path': 'Dossier surveille',
                'success_folder_path': 'Dossier succes',
                'error_folder_path': 'Dossier erreur',
                'rejected_folder_path': 'Dossier rejete',
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

                # Verifier chemin absolu
                if not path.is_absolute():
                    raise ValidationError(
                        f"{field_label}: Le chemin doit etre absolu. "
                        f"Valeur actuelle: {path_str}"
                    )

                # Verifier existence du parent
                parent = path.parent
                if not parent.exists():
                    raise ValidationError(
                        f"{field_label}: Le repertoire parent n'existe pas. "
                        f"Parent attendu: {parent}"
                    )

                # Verifier permissions
                if not os.access(str(parent), os.R_OK | os.W_OK):
                    raise ValidationError(
                        f"{field_label}: Permissions insuffisantes (lecture/ecriture requises). "
                        f"Chemin: {path_str}"
                    )

    @api.model
    @tools.ormcache()
    def get_config(self):
        """Retourne l'enregistrement de configuration unique (le cree si necessaire)

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
        """Retourne la liste des modeles disponibles pour le champ Selection.

        Cette methode peut etre appelee par Odoo meme si self est vide ou non initialise.
        Elle recupere automatiquement le config singleton si necessaire.

        Called automatically by Odoo when rendering the Selection field.
        Fetches available models from Ollama API and formats them for the dropdown.

        Returns:
            list: Liste de tuples (value, label) pour le champ Selection.
                  Retourne au moins le modele par defaut si aucun modele disponible.
        """
        # Recuperer le config singleton pour avoir acces a ollama_url
        # Ceci fonctionne meme si self est vide ou pas encore cree
        if self:
            config = self
        else:
            # Si self est vide, rechercher le singleton existant
            config = self.env['jsocr.config'].sudo().search([], limit=1)
            if not config:
                # Aucun config n'existe encore, retourner le defaut
                return [('llama3', 'llama3 (defaut)')]

        # Recuperer les modeles disponibles
        models = config._fetch_available_models()
        if not models:
            # Fallback: retourner au moins le modele par defaut
            return [('llama3', 'llama3 (defaut)')]

        return [(model, model) for model in models]

    def _fetch_available_models(self):
        """Recupere les modeles disponibles depuis Ollama API.

        Calls GET /api/tags endpoint silently (no user errors raised).
        Used to populate the Selection field dropdown.

        Returns:
            list: Liste des noms de modeles, ou liste vide si erreur
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
            raise UserError("L'URL Ollama n'est pas configuree")

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
                    message = f"Connexion OK - Modeles disponibles: {', '.join(models)}"
                else:
                    message = "Connexion OK - Aucun modele disponible"

                _logger.info(f"JSOCR: Ollama connection successful - {len(models)} model(s) found")

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Succes',
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
            error_msg = "Erreur de connexion: Timeout apres 10s"
            _logger.warning("JSOCR: Ollama connection timeout")
            raise UserError(error_msg)

        except requests.ConnectionError:
            error_msg = "Erreur de connexion au serveur Ollama"
            _logger.error("JSOCR: Ollama connection error")
            raise UserError(error_msg)

        except ValueError:
            error_msg = "Erreur: Reponse JSON invalide du serveur Ollama"
            _logger.error("JSOCR: Invalid JSON response from Ollama")
            raise UserError(error_msg)
        except KeyError:
            error_msg = "Erreur: Structure de reponse invalide du serveur Ollama"
            _logger.error("JSOCR: Invalid response structure from Ollama")
            raise UserError(error_msg)
