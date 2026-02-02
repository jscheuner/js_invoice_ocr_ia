# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase
from odoo.exceptions import AccessError


class TestJsocrSecurity(TransactionCase):
    """Tests pour les groupes de sécurité JSOCR et leurs droits d'accès"""

    def setUp(self):
        super().setUp()
        self.JsocrConfig = self.env['jsocr.config']

        # Références aux groupes JSOCR
        self.group_user = self.env.ref('js_invoice_ocr_ia.group_jsocr_user')
        self.group_manager = self.env.ref('js_invoice_ocr_ia.group_jsocr_manager')
        self.group_admin = self.env.ref('js_invoice_ocr_ia.group_jsocr_admin')

        # Groupe de base Odoo pour les utilisateurs internes
        self.group_base_user = self.env.ref('base.group_user')

        # Créer des utilisateurs de test avec différents groupes
        self.user_simple = self.env['res.users'].create({
            'name': 'Test User Simple',
            'login': 'test_user_simple',
            'email': 'user@test.com',
            'groups_id': [(6, 0, [self.group_base_user.id])]
        })

        self.user_ocr = self.env['res.users'].create({
            'name': 'Test User OCR',
            'login': 'test_user_ocr',
            'email': 'userocr@test.com',
            'groups_id': [(6, 0, [self.group_base_user.id, self.group_user.id])]
        })

        self.user_manager = self.env['res.users'].create({
            'name': 'Test Manager OCR',
            'login': 'test_manager_ocr',
            'email': 'manager@test.com',
            'groups_id': [(6, 0, [self.group_base_user.id, self.group_manager.id])]
        })

        self.user_admin = self.env['res.users'].create({
            'name': 'Test Admin OCR',
            'login': 'test_admin_ocr',
            'email': 'admin@test.com',
            'groups_id': [(6, 0, [self.group_base_user.id, self.group_admin.id])]
        })

    def test_assign_group_user(self):
        """Test: assigner groupe Utilisateur OCR à un utilisateur"""
        # Vérifier que l'utilisateur simple n'a pas le groupe OCR
        self.assertFalse(self.user_simple.has_group('js_invoice_ocr_ia.group_jsocr_user'))

        # Assigner le groupe User
        self.user_simple.write({'groups_id': [(4, self.group_user.id)]})

        # Vérifier que l'utilisateur a maintenant le groupe
        self.assertTrue(self.user_simple.has_group('js_invoice_ocr_ia.group_jsocr_user'))

    def test_manager_inherits_user(self):
        """Test: groupe Manager hérite automatiquement de User"""
        # Le user_manager a group_manager assigné dans setUp
        # Il doit aussi avoir automatiquement group_user (via implied_ids)
        self.assertTrue(self.user_manager.has_group('js_invoice_ocr_ia.group_jsocr_manager'))
        self.assertTrue(self.user_manager.has_group('js_invoice_ocr_ia.group_jsocr_user'))

    def test_admin_inherits_manager_and_user(self):
        """Test: groupe Admin hérite de Manager et User"""
        # Le user_admin a group_admin assigné dans setUp
        # Il doit avoir automatiquement group_manager et group_user
        self.assertTrue(self.user_admin.has_group('js_invoice_ocr_ia.group_jsocr_admin'))
        self.assertTrue(self.user_admin.has_group('js_invoice_ocr_ia.group_jsocr_manager'))
        self.assertTrue(self.user_admin.has_group('js_invoice_ocr_ia.group_jsocr_user'))

    def test_user_without_group_no_access_to_config(self):
        """Test: utilisateur sans groupe OCR ne peut pas accéder à la configuration"""
        # Nettoyer les configs existantes
        self.JsocrConfig.sudo().search([]).unlink()

        # Créer une config en tant que sudo
        config = self.JsocrConfig.sudo().create({
            'ollama_url': 'http://test:11434'
        })

        # Utilisateur simple (sans groupe OCR) ne devrait pas pouvoir lire la config
        with self.assertRaises(AccessError):
            self.JsocrConfig.with_user(self.user_simple).browse(config.id).read(['ollama_url'])

    def test_user_ocr_can_read_config(self):
        """Test: utilisateur avec group_user peut lire la configuration (lecture seule)"""
        # Nettoyer les configs existantes
        self.JsocrConfig.sudo().search([]).unlink()

        # Créer une config en tant que sudo
        config = self.JsocrConfig.sudo().create({
            'ollama_url': 'http://test:11434'
        })

        # Utilisateur OCR devrait pouvoir lire
        config_read = self.JsocrConfig.with_user(self.user_ocr).browse(config.id)
        self.assertEqual(config_read.ollama_url, 'http://test:11434')

        # Mais ne devrait pas pouvoir écrire (ACL: read=1, write=0)
        with self.assertRaises(AccessError):
            config_read.write({'ollama_url': 'http://modified:11434'})

    def test_admin_has_full_access_to_config(self):
        """Test: administrateur OCR a accès complet à la configuration"""
        # Nettoyer les configs existantes
        self.JsocrConfig.sudo().search([]).unlink()

        # Créer une config en tant que sudo
        config = self.JsocrConfig.sudo().create({
            'ollama_url': 'http://test:11434'
        })

        # Admin devrait pouvoir lire
        config_read = self.JsocrConfig.with_user(self.user_admin).browse(config.id)
        self.assertEqual(config_read.ollama_url, 'http://test:11434')

        # Admin devrait pouvoir écrire (ACL: read=1, write=1)
        config_read.write({'ollama_url': 'http://modified:11434'})
        self.assertEqual(config_read.ollama_url, 'http://modified:11434')

        # Admin devrait pouvoir créer (ACL: create=1)
        new_config = self.JsocrConfig.with_user(self.user_admin).create({
            'ollama_url': 'http://newconfig:11434'
        })
        self.assertTrue(new_config)

    def test_revoke_group_removes_access(self):
        """Test: révoquer un groupe retire les droits d'accès"""
        # Créer un utilisateur avec group_user
        test_user = self.env['res.users'].create({
            'name': 'Test Revoke User',
            'login': 'test_revoke_user',
            'email': 'revoke@test.com',
            'groups_id': [(6, 0, [self.group_base_user.id, self.group_user.id])]
        })

        # Vérifier qu'il a le groupe
        self.assertTrue(test_user.has_group('js_invoice_ocr_ia.group_jsocr_user'))

        # Révoquer le groupe OCR
        test_user.write({'groups_id': [(3, self.group_user.id)]})

        # Vérifier qu'il n'a plus le groupe
        self.assertFalse(test_user.has_group('js_invoice_ocr_ia.group_jsocr_user'))

        # Vérifier qu'il n'a plus accès à la config
        self.JsocrConfig.sudo().search([]).unlink()
        config = self.JsocrConfig.sudo().create({
            'ollama_url': 'http://test:11434'
        })

        with self.assertRaises(AccessError):
            self.JsocrConfig.with_user(test_user).browse(config.id).read(['ollama_url'])
