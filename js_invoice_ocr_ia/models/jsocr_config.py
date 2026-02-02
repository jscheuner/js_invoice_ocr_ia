# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

import base64
import logging
import os
import re
import requests
import shutil
from datetime import datetime
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
        default='/opt/jsocr/watch',
        required=True,
        help='Chemin du dossier a surveiller pour nouveaux PDFs'
    )

    success_folder_path = fields.Char(
        string='Success Folder',
        default='/opt/jsocr/success',
        required=True,
        help='Chemin du dossier pour fichiers traites avec succes'
    )

    error_folder_path = fields.Char(
        string='Error Folder',
        default='/opt/jsocr/error',
        required=True,
        help='Chemin du dossier pour fichiers en erreur'
    )

    rejected_folder_path = fields.Char(
        string='Rejected Folder',
        default='/opt/jsocr/rejected',
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
        """Validate folder paths and create directories automatically if they don't exist"""
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

                # Creer le repertoire automatiquement s'il n'existe pas
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    _logger.info(f"JSOCR: Directory created or verified: {path_str}")
                except PermissionError:
                    import getpass
                    current_user = getpass.getuser()
                    raise ValidationError(
                        f"{field_label}: Permissions insuffisantes pour creer le repertoire. "
                        f"Chemin: {path_str}. "
                        f"Veuillez creer manuellement avec: sudo mkdir -p {path_str} && sudo chown {current_user}:{current_user} {path_str}"
                    )
                except OSError as e:
                    raise ValidationError(
                        f"{field_label}: Impossible de creer le repertoire. "
                        f"Chemin: {path_str}. "
                        f"Erreur: {str(e)}"
                    )

    @api.model
    def get_config(self):
        """Retourne l'enregistrement de configuration unique (le cree si necessaire)

        Uses sudo() to ensure creation works even for users without create rights.

        Returns:
            jsocr.config: L'enregistrement de configuration unique
        """
        config = self.sudo().search([], limit=1)
        if not config:
            # Use sudo() to create config even if current user lacks create rights
            config = self.sudo().create({})
        return config

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

    # -------------------------------------------------------------------------
    # FOLDER SCANNING (Story 3.4)
    # -------------------------------------------------------------------------

    @api.model
    def scan_input_folder(self):
        """Scan watch folder for new PDFs and create import jobs.

        Called by ir.cron every 5 minutes (ir_cron_jsocr_scan_folder).
        Creates a jsocr.import.job for each PDF found in watch_folder_path.
        Files are removed from watch folder after job creation to prevent
        duplicate processing.

        This method only processes PDF files. Non-PDF files are ignored
        (handled by Story 3.5).

        Returns:
            int: Number of jobs created
        """
        config = self.get_config()

        if not config.watch_folder_path:
            _logger.warning("JSOCR: Watch folder not configured")
            return 0

        watch_path = Path(config.watch_folder_path)

        if not watch_path.exists():
            _logger.warning("JSOCR: Watch folder does not exist: %s", watch_path)
            return 0

        if not watch_path.is_dir():
            _logger.warning("JSOCR: Watch path is not a directory: %s", watch_path)
            return 0

        # Find PDF files (case-insensitive)
        pdf_files = list(watch_path.glob('*.pdf')) + list(watch_path.glob('*.PDF'))
        # Remove duplicates (in case *.pdf and *.PDF match same files on case-insensitive systems)
        pdf_files = list(set(pdf_files))

        _logger.info("JSOCR: Scan found %d PDF file(s) to process", len(pdf_files))

        jobs_created = 0
        for pdf_path in pdf_files:
            try:
                if self._process_pdf_file(pdf_path):
                    jobs_created += 1
            except Exception as e:
                _logger.error(
                    "JSOCR: Failed to process file %s: %s",
                    pdf_path.name, type(e).__name__
                )
                # Continue with other files

        # Handle non-PDF files (Story 3.5)
        all_files = [f for f in watch_path.iterdir() if f.is_file()]
        rejected_count = 0
        for file_path in all_files:
            if file_path.suffix.lower() != '.pdf':
                try:
                    self._reject_non_pdf_file(file_path)
                    rejected_count += 1
                except Exception as e:
                    _logger.error(
                        "JSOCR: Failed to reject file %s: %s",
                        file_path.name, type(e).__name__
                    )

        _logger.info("JSOCR: Scan complete - %d job(s) created, %d file(s) rejected", jobs_created, rejected_count)
        return jobs_created

    def _process_pdf_file(self, pdf_path):
        """Process a single PDF file and create an import job.

        Reads the PDF content, creates a jsocr.import.job in 'pending' state,
        and removes the source file from watch folder.

        Args:
            pdf_path (Path): Path to the PDF file

        Returns:
            bool: True if job created successfully, False otherwise
        """
        if not pdf_path.exists():
            _logger.warning("JSOCR: File no longer exists: %s", pdf_path.name)
            return False

        if not pdf_path.is_file():
            _logger.warning("JSOCR: Path is not a file: %s", pdf_path.name)
            return False

        try:
            # Read PDF content
            pdf_content = pdf_path.read_bytes()
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')

            # Create import job
            job = self.env['jsocr.import.job'].create({
                'pdf_file': pdf_base64,
                'pdf_filename': pdf_path.name,
            })

            # Submit job (draft -> pending)
            job.action_submit()

            _logger.info("JSOCR: Created job %s for file %s", job.id, pdf_path.name)

            # Remove file from watch folder to prevent duplicate processing
            pdf_path.unlink()
            _logger.info("JSOCR: Removed processed file %s", pdf_path.name)

            return True

        except PermissionError:
            _logger.error("JSOCR: Permission denied reading file %s", pdf_path.name)
            return False
        except IOError as e:
            _logger.error("JSOCR: IO error reading file %s: %s", pdf_path.name, str(e))
            return False

    # -------------------------------------------------------------------------
    # NON-PDF FILE REJECTION (Story 3.5)
    # -------------------------------------------------------------------------

    def _reject_non_pdf_file(self, file_path):
        """Reject a non-PDF file by moving it to rejected_folder_path.

        Moves the file to the rejected folder. If a file with the same name
        already exists, adds a timestamp prefix (YYYYMMDD_HHMMSS_) to ensure
        uniqueness. Sends an email alert if alert_email is configured.

        Args:
            file_path (Path): Path to the non-PDF file to reject
        """
        config = self.get_config()
        rejected_path = Path(config.rejected_folder_path)

        # Ensure rejected folder exists
        if not rejected_path.exists():
            rejected_path.mkdir(parents=True, exist_ok=True)

        # Generate destination filename (with timestamp if duplicate)
        dest_name = file_path.name
        dest_path = rejected_path / dest_name

        if dest_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest_name = f"{timestamp}_{file_path.name}"
            dest_path = rejected_path / dest_name

        # Move file to rejected folder
        shutil.move(str(file_path), str(dest_path))
        _logger.info("JSOCR: Rejected non-PDF file: %s", file_path.name)

        # Send alert email if configured
        if config.alert_email:
            self._send_rejection_alert(file_path.name)

    def _send_rejection_alert(self, filename):
        """Send email alert for rejected non-PDF file.

        Creates and sends a mail.mail record to notify the configured
        alert_email address that a file was rejected.

        Args:
            filename (str): Name of the rejected file
        """
        config = self.get_config()
        if not config.alert_email:
            return

        mail_values = {
            'subject': 'JSOCR: Fichier non-PDF rejete',
            'body_html': f'<p>Le fichier <b>{filename}</b> a ete rejete car ce n\'est pas un PDF.</p>',
            'email_to': config.alert_email,
        }

        try:
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.send()
            _logger.info("JSOCR: Rejection alert email sent for file: %s", filename)
        except Exception as e:
            _logger.error("JSOCR: Failed to send rejection alert email: %s", type(e).__name__)
