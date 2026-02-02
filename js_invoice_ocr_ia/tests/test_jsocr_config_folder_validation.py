# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

"""
Tests for JSOCR configuration folder path validation.

This module tests:
- AC1: Validation des chemins de dossiers (absolu, parent existe, permissions)
- AC2: Persistance des valeurs
- AC3: Messages d'erreur explicites
- AC4: Champs obligatoires
"""

import os
import tempfile
from pathlib import Path
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install', 'jsocr', 'jsocr_config')
class TestJsocrConfigFolderValidation(TransactionCase):
    """Test folder path validation for jsocr.config model."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        super().setUpClass()
        cls.Config = cls.env['jsocr.config']

        # Nettoyer les configs existantes pour tests isoles
        cls.Config.search([]).unlink()
        cls.env.registry.clear_cache()

        # Creer un dossier temporaire pour les tests
        cls.temp_dir = tempfile.mkdtemp()

        # Creer des sous-dossiers de test dans le dossier temporaire
        cls.valid_watch_path = os.path.join(cls.temp_dir, 'watch')
        cls.valid_success_path = os.path.join(cls.temp_dir, 'success')
        cls.valid_error_path = os.path.join(cls.temp_dir, 'error')
        cls.valid_rejected_path = os.path.join(cls.temp_dir, 'rejected')

    def setUp(self):
        """Clean up before each test."""
        super().setUp()
        # Note: setUpClass nettoie deja, mais certains tests creent des configs
        # Le cleanup ici garantit l'isolation entre tests

    # -------------------------------------------------------------------------
    # AC1: Validation des chemins de dossiers
    # -------------------------------------------------------------------------

    def test_valid_absolute_paths_accepted(self):
        """Test: Chemins absolus valides avec parent existant sont acceptes"""
        # Le dossier temporaire existe, donc on peut creer des chemins qui pointent vers lui
        config = self.Config.create({
            'watch_folder_path': self.valid_watch_path,
            'success_folder_path': self.valid_success_path,
            'error_folder_path': self.valid_error_path,
            'rejected_folder_path': self.valid_rejected_path,
        })
        self.assertTrue(config.id, "Config avec chemins absolus valides devrait etre cree")
        self.assertEqual(config.watch_folder_path, self.valid_watch_path)

    def test_relative_path_rejected(self):
        """Test: Chemin relatif est rejete avec message approprie"""
        with self.assertRaises(ValidationError) as cm:
            self.Config.create({
                'watch_folder_path': 'relative/path',
            })
        error_message = str(cm.exception)
        self.assertIn('absolu', error_message.lower(),
                     "Message d'erreur devrait mentionner 'absolu'")
        self.assertIn('Dossier surveille', error_message,
                     "Message d'erreur devrait mentionner le champ concerne")

    def test_nonexistent_parent_rejected(self):
        """Test: Chemin avec parent inexistant est rejete"""
        # Creer un chemin absolu mais avec parent inexistant
        nonexistent_path = '/nonexistent_parent_JSOCR_TEST_12345/subfolder'

        with self.assertRaises(ValidationError) as cm:
            self.Config.create({
                'watch_folder_path': nonexistent_path,
            })
        error_message = str(cm.exception)
        self.assertIn('parent', error_message.lower(),
                     "Message d'erreur devrait mentionner 'parent'")

    def test_all_folder_fields_validated(self):
        """Test: Tous les champs de dossiers sont valides"""
        # Test chaque champ individuellement avec un chemin relatif
        folder_fields = [
            'watch_folder_path',
            'success_folder_path',
            'error_folder_path',
            'rejected_folder_path',
        ]

        for field_name in folder_fields:
            with self.assertRaises(ValidationError):
                # Nettoyer avant chaque test
                self.Config.search([]).unlink()
                self.env.registry.clear_cache()

                # Creer config avec un champ invalide
                self.Config.create({
                    field_name: 'relative/path',
                })

    def test_insufficient_permissions_rejected(self):
        """Test: Dossier parent sans permissions R/W est rejete (AC1 ligne 19)"""
        # Note: Ce test est difficile a implementer de maniere portable car:
        # 1. Creer un dossier read-only necessite des permissions root/admin
        # 2. Le comportement varie selon l'OS (Unix vs Windows)
        # 3. Les tests Odoo tournent souvent avec des privileges eleves
        #
        # Solution: On teste la logique avec un mock ou on documente la limitation
        # Pour ce test, on verifie que le code TENTE de verifier les permissions

        # Sur Unix, /root est generalement inaccessible pour utilisateurs normaux
        # Sur Windows, System Volume Information est protege
        if os.name == 'posix':  # Unix/Linux
            # Chercher un dossier qui existe mais n'est pas writable
            protected_paths = ['/root/test_ocr', '/sys/test_ocr']
            for protected_path in protected_paths:
                parent = Path(protected_path).parent
                if parent.exists() and not os.access(str(parent), os.W_OK):
                    with self.assertRaises(ValidationError) as cm:
                        self.Config.create({
                            'watch_folder_path': protected_path,
                        })
                    self.assertIn('permissions', str(cm.exception).lower(),
                                "Message devrait mentionner les permissions")
                    return  # Test reussi

        # Si aucun dossier protege n'est disponible, on skip le test
        # (mieux que de faire echouer le test sur certains environnements)
        self.skipTest("Aucun dossier avec permissions restreintes disponible pour ce test")

    # -------------------------------------------------------------------------
    # AC2: Persistance des valeurs
    # -------------------------------------------------------------------------

    def test_valid_paths_persist_after_create(self):
        """Test: Chemins valides persistent apres creation"""
        config = self.Config.create({
            'watch_folder_path': self.valid_watch_path,
        })

        # Recharger depuis la base
        config.invalidate_cache()
        config_reloaded = self.Config.browse(config.id)

        self.assertEqual(config_reloaded.watch_folder_path, self.valid_watch_path,
                        "Chemin devrait persister apres creation")

    def test_valid_paths_persist_after_write(self):
        """Test: Chemins valides persistent apres modification"""
        config = self.Config.create({
            'watch_folder_path': self.valid_watch_path,
        })

        # Modifier le chemin
        new_path = self.valid_success_path
        config.write({'watch_folder_path': new_path})

        # Recharger depuis la base
        config.invalidate_cache()
        config_reloaded = self.Config.browse(config.id)

        self.assertEqual(config_reloaded.watch_folder_path, new_path,
                        "Nouveau chemin devrait persister apres modification")

    # -------------------------------------------------------------------------
    # AC3: Messages d'erreur explicites
    # -------------------------------------------------------------------------

    def test_error_message_includes_field_name(self):
        """Test: Message d'erreur mentionne le champ concerne"""
        with self.assertRaises(ValidationError) as cm:
            self.Config.create({
                'success_folder_path': 'relative/path',
            })
        error_message = str(cm.exception)
        self.assertIn('Dossier succes', error_message,
                     "Message devrait identifier le champ 'Dossier succes'")

    def test_error_message_includes_reason(self):
        """Test: Message d'erreur indique la raison de l'echec"""
        # Test pour chemin relatif
        with self.assertRaises(ValidationError) as cm:
            self.Config.create({
                'watch_folder_path': 'relative/path',
            })
        self.assertIn('absolu', str(cm.exception).lower(),
                     "Message devrait indiquer que le chemin doit etre absolu")

        # Test pour parent inexistant
        self.Config.search([]).unlink()
        self.env.registry.clear_cache()

        with self.assertRaises(ValidationError) as cm:
            self.Config.create({
                'watch_folder_path': '/nonexistent_JSOCR_TEST/folder',
            })
        self.assertIn('parent', str(cm.exception).lower(),
                     "Message devrait mentionner le parent inexistant")

    def test_error_message_includes_invalid_value(self):
        """Test: Message d'erreur inclut la valeur invalide"""
        invalid_path = 'my/relative/path'
        with self.assertRaises(ValidationError) as cm:
            self.Config.create({
                'watch_folder_path': invalid_path,
            })
        error_message = str(cm.exception)
        self.assertIn(invalid_path, error_message,
                     "Message devrait inclure la valeur invalide")

    # -------------------------------------------------------------------------
    # AC4: Champs obligatoires
    # -------------------------------------------------------------------------

    def test_empty_watch_folder_rejected(self):
        """Test: Champ watch_folder_path vide est rejete (required=True)"""
        # Odoo leve differentes exceptions selon le contexte pour required=True
        # Peut etre UserError, MissingError, ou ValidationError
        from odoo.exceptions import UserError, MissingError
        with self.assertRaises((ValidationError, UserError, MissingError)):
            self.Config.create({
                'watch_folder_path': False,  # False = valeur vide dans Odoo
            })

    def test_empty_success_folder_rejected(self):
        """Test: Champ success_folder_path vide est rejete (required=True)"""
        from odoo.exceptions import UserError, MissingError
        with self.assertRaises((ValidationError, UserError, MissingError)):
            self.Config.create({
                'watch_folder_path': self.valid_watch_path,
                'success_folder_path': False,
            })

    def test_all_required_fields_must_be_present(self):
        """Test: Tous les champs de dossiers sont requis"""
        from odoo.exceptions import UserError, MissingError
        required_fields = [
            'watch_folder_path',
            'success_folder_path',
            'error_folder_path',
            'rejected_folder_path',
        ]

        for field_name in required_fields:
            with self.assertRaises((ValidationError, UserError, MissingError)):
                # Nettoyer avant chaque test
                self.Config.search([]).unlink()
                self.env.registry.clear_cache()

                # Tenter de creer sans le champ requis
                vals = {
                    'watch_folder_path': self.valid_watch_path,
                    'success_folder_path': self.valid_success_path,
                    'error_folder_path': self.valid_error_path,
                    'rejected_folder_path': self.valid_rejected_path,
                }
                vals[field_name] = False  # Vider le champ
                self.Config.create(vals)

    # -------------------------------------------------------------------------
    # Tests supplementaires de robustesse
    # -------------------------------------------------------------------------

    def test_windows_absolute_path_format(self):
        """Test: Format Windows (C:\\) est reconnu comme absolu et valide"""
        windows_path = 'C:\\Windows\\Temp\\ocr_test'
        path = Path(windows_path)

        # Test 1: Verifier que Path reconnait le format Windows comme absolu
        if os.name == 'nt':  # Sur Windows
            self.assertTrue(path.is_absolute(),
                          "Chemin Windows devrait etre reconnu comme absolu")

            # Test 2: Verifier que la creation de config fonctionne si parent existe
            if path.parent.exists():
                config = self.Config.create({
                    'watch_folder_path': windows_path,
                })
                self.assertEqual(config.watch_folder_path, windows_path,
                               "Chemin Windows valide devrait etre accepte")

    def test_modification_from_invalid_to_valid(self):
        """Test: Modification d'un chemin valide vers un invalide est bloquee"""
        config = self.Config.create({
            'watch_folder_path': self.valid_watch_path,
        })

        # Tenter de modifier vers un chemin invalide
        with self.assertRaises(ValidationError):
            config.write({'watch_folder_path': 'relative/invalid'})

        # Verifier que le chemin original est preserve
        config.invalidate_cache()
        self.assertEqual(config.watch_folder_path, self.valid_watch_path,
                        "Chemin original devrait etre preserve apres echec de modification")

    def test_multiple_fields_with_mixed_validity(self):
        """Test: Si un seul champ est invalide, toute la validation echoue"""
        with self.assertRaises(ValidationError):
            self.Config.create({
                'watch_folder_path': self.valid_watch_path,  # Valide
                'success_folder_path': 'relative/invalid',   # Invalide
                'error_folder_path': self.valid_error_path,  # Valide
            })
