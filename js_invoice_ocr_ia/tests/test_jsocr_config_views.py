# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

"""
Tests for JSOCR configuration views and menu.

This module tests:
- AC1: Menu visibility for admin only
- AC2: Form view displays all configuration fields
- AC3: Modification and save functionality
- AC4: Default values displayed correctly
"""

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install', 'jsocr', 'jsocr_views')
class TestJsocrConfigViews(TransactionCase):
    """Test configuration views and menu security."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        super().setUpClass()
        cls.admin_group = cls.env.ref('js_invoice_ocr_ia.group_jsocr_admin')
        cls.manager_group = cls.env.ref('js_invoice_ocr_ia.group_jsocr_manager')
        cls.user_group = cls.env.ref('js_invoice_ocr_ia.group_jsocr_user')

        # Create admin user
        cls.admin_user = cls.env['res.users'].create({
            'name': 'JSOCR Admin Test',
            'login': 'jsocr_admin_test',
            'email': 'admin_test@example.com',
            'groups_id': [(6, 0, [
                cls.admin_group.id,
                cls.env.ref('base.group_user').id,
            ])],
        })

        # Create manager user
        cls.manager_user = cls.env['res.users'].create({
            'name': 'JSOCR Manager Test',
            'login': 'jsocr_manager_test',
            'email': 'manager_test@example.com',
            'groups_id': [(6, 0, [
                cls.manager_group.id,
                cls.env.ref('base.group_user').id,
            ])],
        })

        # Create standard user
        cls.standard_user = cls.env['res.users'].create({
            'name': 'JSOCR User Test',
            'login': 'jsocr_user_test',
            'email': 'user_test@example.com',
            'groups_id': [(6, 0, [
                cls.user_group.id,
                cls.env.ref('base.group_user').id,
            ])],
        })

    # -------------------------------------------------------------------------
    # AC1: Menu Configuration visible pour admin uniquement
    # -------------------------------------------------------------------------

    def test_menu_root_exists(self):
        """Test that root OCR IA menu exists."""
        menu = self.env.ref('js_invoice_ocr_ia.menu_jsocr_root', raise_if_not_found=False)
        self.assertTrue(menu, "Root menu 'OCR IA' should exist")

    def test_menu_configuration_exists(self):
        """Test that configuration submenu exists."""
        menu = self.env.ref('js_invoice_ocr_ia.menu_jsocr_configuration', raise_if_not_found=False)
        self.assertTrue(menu, "Configuration submenu should exist")

    def test_menu_config_exists(self):
        """Test that system configuration menu exists."""
        menu = self.env.ref('js_invoice_ocr_ia.menu_jsocr_config', raise_if_not_found=False)
        self.assertTrue(menu, "System configuration menu should exist")

    def test_menu_restricted_to_admin(self):
        """Test that system configuration menu is restricted to admin group."""
        menu = self.env.ref('js_invoice_ocr_ia.menu_jsocr_config')
        # Check menu has groups restriction
        self.assertTrue(menu.groups_id, "Menu should have groups restriction")
        # Check only admin group has access
        self.assertEqual(len(menu.groups_id), 1, "Menu should have exactly one group")
        self.assertEqual(menu.groups_id, self.admin_group, "Menu should only be accessible to admin group")

    def test_menu_not_visible_for_user(self):
        """Test that standard user cannot see admin menu."""
        menu = self.env.ref('js_invoice_ocr_ia.menu_jsocr_config')
        # User should not be in menu's groups
        self.assertNotIn(self.user_group, menu.groups_id)

    def test_menu_not_visible_for_manager(self):
        """Test that manager cannot see admin menu."""
        menu = self.env.ref('js_invoice_ocr_ia.menu_jsocr_config')
        # Manager should not be in menu's groups
        self.assertNotIn(self.manager_group, menu.groups_id)

    # -------------------------------------------------------------------------
    # AC2: Formulaire de configuration complet
    # -------------------------------------------------------------------------

    def test_form_view_exists(self):
        """Test that form view exists."""
        view = self.env.ref('js_invoice_ocr_ia.jsocr_config_view_form', raise_if_not_found=False)
        self.assertTrue(view, "Form view should exist")
        self.assertEqual(view.model, 'jsocr.config', "View should be for jsocr.config model")
        self.assertEqual(view.type, 'form', "View type should be form")

    def test_form_displays_ollama_fields(self):
        """Test that form view contains Ollama configuration fields."""
        view = self.env.ref('js_invoice_ocr_ia.jsocr_config_view_form')
        arch = view.arch
        # Check Ollama section fields
        self.assertIn('ollama_url', arch, "Form should display ollama_url field")
        self.assertIn('ollama_model', arch, "Form should display ollama_model field")
        self.assertIn('ollama_timeout', arch, "Form should display ollama_timeout field")

    def test_form_displays_folder_fields(self):
        """Test that form view contains folder path fields."""
        view = self.env.ref('js_invoice_ocr_ia.jsocr_config_view_form')
        arch = view.arch
        # Check folder section fields
        self.assertIn('watch_folder_path', arch, "Form should display watch_folder_path field")
        self.assertIn('success_folder_path', arch, "Form should display success_folder_path field")
        self.assertIn('error_folder_path', arch, "Form should display error_folder_path field")
        self.assertIn('rejected_folder_path', arch, "Form should display rejected_folder_path field")

    def test_form_displays_alert_fields(self):
        """Test that form view contains alert configuration fields."""
        view = self.env.ref('js_invoice_ocr_ia.jsocr_config_view_form')
        arch = view.arch
        # Check alert section fields
        self.assertIn('alert_amount_threshold', arch, "Form should display alert_amount_threshold field")
        self.assertIn('alert_email', arch, "Form should display alert_email field")

    def test_action_exists(self):
        """Test that server action exists and opens singleton."""
        action = self.env.ref('js_invoice_ocr_ia.jsocr_config_action', raise_if_not_found=False)
        self.assertTrue(action, "Server action should exist")
        # Check it's a server action targeting jsocr.config model
        self.assertEqual(action._name, 'ir.actions.server', "Action should be a server action for singleton access")
        self.assertEqual(action.model_id.model, 'jsocr.config', "Action should target jsocr.config model")

    # -------------------------------------------------------------------------
    # AC3: Modification et sauvegarde fonctionnelles
    # -------------------------------------------------------------------------

    def test_admin_can_create_and_modify_config(self):
        """Test that admin can create and modify configuration."""
        # Create config as admin
        ConfigModel = self.env['jsocr.config'].with_user(self.admin_user)
        config = ConfigModel.create({
            'ollama_url': 'http://test:11434',
        })
        self.assertTrue(config.id, "Admin should be able to create config")

        # Modify config
        config.write({
            'ollama_model': 'mistral',
            'alert_amount_threshold': 15000.0,
        })
        self.assertEqual(config.ollama_model, 'mistral', "Modification should be persisted")
        self.assertEqual(config.alert_amount_threshold, 15000.0, "Modification should be persisted")

    def test_user_cannot_modify_config(self):
        """Test that standard user cannot modify configuration."""
        # Create config as admin first
        config = self.env['jsocr.config'].create({
            'ollama_url': 'http://test:11434',
        })

        # Try to modify as user
        config_as_user = config.with_user(self.standard_user)
        with self.assertRaises(AccessError):
            config_as_user.write({'ollama_model': 'llama3'})

    def test_manager_cannot_modify_config(self):
        """Test that manager cannot modify configuration."""
        # Create config as admin first
        config = self.env['jsocr.config'].create({
            'ollama_url': 'http://test:11434',
        })

        # Try to modify as manager
        config_as_manager = config.with_user(self.manager_user)
        with self.assertRaises(AccessError):
            config_as_manager.write({'ollama_model': 'llama3'})

    # -------------------------------------------------------------------------
    # AC4: Valeurs par defaut visibles
    # -------------------------------------------------------------------------

    def test_default_ollama_url(self):
        """Test that default ollama_url is set correctly."""
        config = self.env['jsocr.config'].create({})
        self.assertEqual(config.ollama_url, 'http://localhost:11434',
                        "Default ollama_url should be http://localhost:11434")

    def test_default_ollama_model(self):
        """Test that default ollama_model is set correctly."""
        config = self.env['jsocr.config'].create({})
        self.assertEqual(config.ollama_model, 'llama3',
                        "Default ollama_model should be llama3")

    def test_default_watch_folder_path(self):
        """Test that default watch_folder_path is set correctly."""
        config = self.env['jsocr.config'].create({})
        self.assertEqual(config.watch_folder_path, '/opt/odoo/ocr_input',
                        "Default watch_folder_path should be /opt/odoo/ocr_input")

    def test_default_alert_amount_threshold(self):
        """Test that default alert_amount_threshold is set correctly."""
        config = self.env['jsocr.config'].create({})
        self.assertEqual(config.alert_amount_threshold, 10000.0,
                        "Default alert_amount_threshold should be 10000.0")

    def test_all_default_values_present(self):
        """Test that all default values are set when creating config."""
        config = self.env['jsocr.config'].create({})
        # Ollama defaults
        self.assertEqual(config.ollama_url, 'http://localhost:11434')
        self.assertEqual(config.ollama_model, 'llama3')
        self.assertEqual(config.ollama_timeout, 120)
        # Folder defaults
        self.assertEqual(config.watch_folder_path, '/opt/odoo/ocr_input')
        self.assertEqual(config.success_folder_path, '/opt/odoo/ocr_success')
        self.assertEqual(config.error_folder_path, '/opt/odoo/ocr_error')
        self.assertEqual(config.rejected_folder_path, '/opt/odoo/ocr_rejected')
        # Alert defaults
        self.assertEqual(config.alert_amount_threshold, 10000.0)
        self.assertFalse(config.alert_email, "alert_email should have no default")

    def test_singleton_behavior(self):
        """Test that configuration behaves as singleton."""
        config1 = self.env['jsocr.config'].create({'ollama_url': 'http://test1:11434'})
        config2 = self.env['jsocr.config'].get_config()
        # Should return the same record
        self.assertEqual(config1.id, config2.id, "get_config() should return the existing singleton")
