# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

"""
Tests for JSOCR security groups and ACL.

This module tests:
- Security groups existence and naming (AC1)
- Group hierarchy with implied_ids (AC2)
- ACL definitions for all models (AC3)
- User rights (AC4)
- Manager rights (AC5)
- Admin rights (AC6)
"""

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install', 'jsocr', 'jsocr_security')
class TestJsocrSecurityGroups(TransactionCase):
    """Test security groups existence and hierarchy."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        super().setUpClass()
        cls.user_group = cls.env.ref('js_invoice_ocr_ia.group_jsocr_user')
        cls.manager_group = cls.env.ref('js_invoice_ocr_ia.group_jsocr_manager')
        cls.admin_group = cls.env.ref('js_invoice_ocr_ia.group_jsocr_admin')
        cls.category = cls.env.ref('js_invoice_ocr_ia.module_category_jsocr')

    # -------------------------------------------------------------------------
    # AC1: Three security groups created
    # -------------------------------------------------------------------------

    def test_user_group_exists(self):
        """Test that group_jsocr_user exists."""
        self.assertTrue(self.user_group, "group_jsocr_user should exist")

    def test_manager_group_exists(self):
        """Test that group_jsocr_manager exists."""
        self.assertTrue(self.manager_group, "group_jsocr_manager should exist")

    def test_admin_group_exists(self):
        """Test that group_jsocr_admin exists."""
        self.assertTrue(self.admin_group, "group_jsocr_admin should exist")

    def test_user_group_name(self):
        """Test that group_jsocr_user has correct name."""
        self.assertEqual(self.user_group.name, 'JSOCR / User')

    def test_manager_group_name(self):
        """Test that group_jsocr_manager has correct name."""
        self.assertEqual(self.manager_group.name, 'JSOCR / Manager')

    def test_admin_group_name(self):
        """Test that group_jsocr_admin has correct name."""
        self.assertEqual(self.admin_group.name, 'JSOCR / Admin')

    def test_category_exists(self):
        """Test that module category exists."""
        self.assertTrue(self.category, "module_category_jsocr should exist")

    def test_category_name(self):
        """Test that category has correct name."""
        self.assertEqual(self.category.name, 'Invoice OCR IA')

    def test_groups_in_category(self):
        """Test that all groups are in the JSOCR category."""
        self.assertEqual(self.user_group.category_id, self.category)
        self.assertEqual(self.manager_group.category_id, self.category)
        self.assertEqual(self.admin_group.category_id, self.category)

    # -------------------------------------------------------------------------
    # AC2: Group hierarchy respected
    # -------------------------------------------------------------------------

    def test_manager_implies_user(self):
        """Test that manager group implies user group."""
        self.assertIn(
            self.user_group,
            self.manager_group.implied_ids,
            "Manager should imply User"
        )

    def test_admin_implies_manager(self):
        """Test that admin group implies manager group."""
        self.assertIn(
            self.manager_group,
            self.admin_group.implied_ids,
            "Admin should imply Manager"
        )

    def test_admin_transitively_implies_user(self):
        """Test that admin transitively gets user rights via manager."""
        # Admin implies Manager, Manager implies User
        # So admin_group.trans_implied_ids should contain user_group
        trans_implied = self.admin_group.trans_implied_ids
        self.assertIn(
            self.user_group,
            trans_implied,
            "Admin should transitively imply User"
        )


@tagged('post_install', '-at_install', 'jsocr', 'jsocr_security')
class TestJsocrACL(TransactionCase):
    """Test ACL definitions for all JSOCR models."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        super().setUpClass()
        cls.AccessModel = cls.env['ir.model.access']
        cls.user_group = cls.env.ref('js_invoice_ocr_ia.group_jsocr_user')
        cls.manager_group = cls.env.ref('js_invoice_ocr_ia.group_jsocr_manager')
        cls.admin_group = cls.env.ref('js_invoice_ocr_ia.group_jsocr_admin')

        # Get model references
        cls.config_model = cls.env['ir.model']._get('jsocr.config')
        cls.job_model = cls.env['ir.model']._get('jsocr.import.job')
        cls.mask_model = cls.env['ir.model']._get('jsocr.mask')
        cls.correction_model = cls.env['ir.model']._get('jsocr.correction')

    # -------------------------------------------------------------------------
    # AC3: ACL defined for all models
    # -------------------------------------------------------------------------

    def test_config_has_three_acl_rules(self):
        """Test that jsocr.config has ACL for all three groups."""
        rules = self.AccessModel.search([
            ('model_id', '=', self.config_model.id),
            ('group_id', 'in', [
                self.user_group.id,
                self.manager_group.id,
                self.admin_group.id
            ])
        ])
        self.assertEqual(len(rules), 3, "jsocr.config should have 3 ACL rules")

    def test_job_has_three_acl_rules(self):
        """Test that jsocr.import.job has ACL for all three groups."""
        rules = self.AccessModel.search([
            ('model_id', '=', self.job_model.id),
            ('group_id', 'in', [
                self.user_group.id,
                self.manager_group.id,
                self.admin_group.id
            ])
        ])
        self.assertEqual(len(rules), 3, "jsocr.import.job should have 3 ACL rules")

    def test_mask_has_three_acl_rules(self):
        """Test that jsocr.mask has ACL for all three groups."""
        rules = self.AccessModel.search([
            ('model_id', '=', self.mask_model.id),
            ('group_id', 'in', [
                self.user_group.id,
                self.manager_group.id,
                self.admin_group.id
            ])
        ])
        self.assertEqual(len(rules), 3, "jsocr.mask should have 3 ACL rules")

    def test_correction_has_three_acl_rules(self):
        """Test that jsocr.correction has ACL for all three groups."""
        rules = self.AccessModel.search([
            ('model_id', '=', self.correction_model.id),
            ('group_id', 'in', [
                self.user_group.id,
                self.manager_group.id,
                self.admin_group.id
            ])
        ])
        self.assertEqual(len(rules), 3, "jsocr.correction should have 3 ACL rules")


@tagged('post_install', '-at_install', 'jsocr', 'jsocr_security')
class TestJsocrUserRights(TransactionCase):
    """Test User group rights (AC4)."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures with a test user."""
        super().setUpClass()
        cls.user_group = cls.env.ref('js_invoice_ocr_ia.group_jsocr_user')

        # Create a test user with only JSOCR User group
        cls.test_user = cls.env['res.users'].create({
            'name': 'JSOCR Test User',
            'login': 'jsocr_test_user',
            'email': 'jsocr_test_user@example.com',
            'groups_id': [(6, 0, [
                cls.user_group.id,
                cls.env.ref('base.group_user').id,  # Internal User
            ])],
        })

        # Create test records with admin
        # jsocr.config is a singleton - no 'name' or 'ocr_engine' fields
        cls.config = cls.env['jsocr.config'].create({
            'ollama_url': 'http://localhost:11434',
        })

        # jsocr.import.job - 'name' is computed, use 'pdf_file' not 'pdf_content'
        cls.job = cls.env['jsocr.import.job'].create({
            'pdf_filename': 'test.pdf',
            'pdf_file': b'test',
            'state': 'pending',
        })

        # jsocr.mask - uses 'mask_data' JSON, not 'field_name'/'pattern'
        partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.mask = cls.env['jsocr.mask'].create({
            'name': 'Test Mask',
            'partner_id': partner.id,
            'mask_data': '{"version": 1, "fields": {}}',
        })

        cls.correction = cls.env['jsocr.correction'].create({
            'import_job_id': cls.job.id,
            'field_name': 'supplier',
            'original_value': 'Old Name',
            'corrected_value': 'New Name',
            'correction_type': 'supplier_alias',
        })

    # -------------------------------------------------------------------------
    # AC4: User rights - jsocr.config
    # -------------------------------------------------------------------------

    def test_user_can_read_config(self):
        """Test that user can read jsocr.config."""
        config_as_user = self.config.with_user(self.test_user)
        # Should not raise AccessError - read ollama_url (config has no 'name')
        url = config_as_user.ollama_url
        self.assertEqual(url, 'http://localhost:11434')

    def test_user_cannot_write_config(self):
        """Test that user cannot write jsocr.config."""
        config_as_user = self.config.with_user(self.test_user)
        with self.assertRaises(AccessError):
            config_as_user.write({'ollama_url': 'http://other:11434'})

    def test_user_cannot_create_config(self):
        """Test that user cannot create jsocr.config."""
        ConfigModel = self.env['jsocr.config'].with_user(self.test_user)
        with self.assertRaises(AccessError):
            ConfigModel.create({
                'ollama_url': 'http://localhost:11434',
            })

    def test_user_cannot_unlink_config(self):
        """Test that user cannot delete jsocr.config."""
        config_as_user = self.config.with_user(self.test_user)
        with self.assertRaises(AccessError):
            config_as_user.unlink()

    # -------------------------------------------------------------------------
    # AC4: User rights - jsocr.import.job
    # -------------------------------------------------------------------------

    def test_user_can_read_job(self):
        """Test that user can read jsocr.import.job."""
        job_as_user = self.job.with_user(self.test_user)
        # name is computed from id and filename
        filename = job_as_user.pdf_filename
        self.assertEqual(filename, 'test.pdf')

    def test_user_can_write_job(self):
        """Test that user can write jsocr.import.job (for validation)."""
        job_as_user = self.job.with_user(self.test_user)
        # Should not raise AccessError
        job_as_user.write({'state': 'processing'})
        self.assertEqual(job_as_user.state, 'processing')

    def test_user_cannot_create_job(self):
        """Test that user cannot create jsocr.import.job."""
        JobModel = self.env['jsocr.import.job'].with_user(self.test_user)
        with self.assertRaises(AccessError):
            JobModel.create({
                'pdf_filename': 'new.pdf',
                'pdf_file': b'new',
                'state': 'pending',
            })

    def test_user_cannot_unlink_job(self):
        """Test that user cannot delete jsocr.import.job."""
        job_as_user = self.job.with_user(self.test_user)
        with self.assertRaises(AccessError):
            job_as_user.unlink()

    # -------------------------------------------------------------------------
    # AC4: User rights - jsocr.mask
    # -------------------------------------------------------------------------

    def test_user_can_read_mask(self):
        """Test that user can read jsocr.mask."""
        mask_as_user = self.mask.with_user(self.test_user)
        name = mask_as_user.name
        self.assertEqual(name, 'Test Mask')

    def test_user_cannot_write_mask(self):
        """Test that user cannot write jsocr.mask."""
        mask_as_user = self.mask.with_user(self.test_user)
        with self.assertRaises(AccessError):
            mask_as_user.write({'mask_data': '{"version": 2}'})

    def test_user_cannot_create_mask(self):
        """Test that user cannot create jsocr.mask."""
        MaskModel = self.env['jsocr.mask'].with_user(self.test_user)
        partner = self.env['res.partner'].create({'name': 'New Partner'})
        with self.assertRaises(AccessError):
            MaskModel.create({
                'name': 'New Mask',
                'partner_id': partner.id,
                'mask_data': '{}',
            })

    def test_user_cannot_unlink_mask(self):
        """Test that user cannot delete jsocr.mask."""
        mask_as_user = self.mask.with_user(self.test_user)
        with self.assertRaises(AccessError):
            mask_as_user.unlink()

    # -------------------------------------------------------------------------
    # AC4: User rights - jsocr.correction
    # -------------------------------------------------------------------------

    def test_user_can_read_correction(self):
        """Test that user can read jsocr.correction."""
        correction_as_user = self.correction.with_user(self.test_user)
        field_name = correction_as_user.field_name
        self.assertEqual(field_name, 'supplier')

    def test_user_can_write_correction(self):
        """Test that user can write jsocr.correction."""
        correction_as_user = self.correction.with_user(self.test_user)
        correction_as_user.write({'corrected_value': 'Updated Name'})
        self.assertEqual(correction_as_user.corrected_value, 'Updated Name')

    def test_user_can_create_correction(self):
        """Test that user can create jsocr.correction."""
        CorrectionModel = self.env['jsocr.correction'].with_user(self.test_user)
        correction = CorrectionModel.create({
            'import_job_id': self.job.id,
            'field_name': 'date',
            'original_value': '2026-01-01',
            'corrected_value': '2026-01-15',
            'correction_type': 'field_value',
        })
        self.assertTrue(correction.id)

    def test_user_cannot_unlink_correction(self):
        """Test that user cannot delete jsocr.correction."""
        correction_as_user = self.correction.with_user(self.test_user)
        with self.assertRaises(AccessError):
            correction_as_user.unlink()


@tagged('post_install', '-at_install', 'jsocr', 'jsocr_security')
class TestJsocrManagerRights(TransactionCase):
    """Test Manager group rights (AC5)."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures with a test manager."""
        super().setUpClass()
        cls.manager_group = cls.env.ref('js_invoice_ocr_ia.group_jsocr_manager')

        # Create a test manager with JSOCR Manager group
        cls.test_manager = cls.env['res.users'].create({
            'name': 'JSOCR Test Manager',
            'login': 'jsocr_test_manager',
            'email': 'jsocr_test_manager@example.com',
            'groups_id': [(6, 0, [
                cls.manager_group.id,
                cls.env.ref('base.group_user').id,  # Internal User
            ])],
        })

        # Create test records with admin
        # jsocr.config is a singleton - no 'name' or 'ocr_engine' fields
        cls.config = cls.env['jsocr.config'].create({
            'ollama_url': 'http://localhost:11434',
            'ollama_model': 'llama3',
        })

        # jsocr.import.job - 'name' is computed, use 'pdf_file' not 'pdf_content'
        cls.job = cls.env['jsocr.import.job'].create({
            'pdf_filename': 'manager_test.pdf',
            'pdf_file': b'test',
            'state': 'pending',
        })

        cls.partner = cls.env['res.partner'].create({'name': 'Manager Test Partner'})
        # jsocr.mask - uses 'mask_data' JSON, not 'field_name'/'pattern'
        cls.mask = cls.env['jsocr.mask'].create({
            'name': 'Manager Test Mask',
            'partner_id': cls.partner.id,
            'mask_data': '{"version": 1, "fields": {"total": {}}}',
        })

        cls.correction = cls.env['jsocr.correction'].create({
            'import_job_id': cls.job.id,
            'field_name': 'supplier',
            'original_value': 'Old Name',
            'corrected_value': 'New Name',
            'correction_type': 'supplier_alias',
        })

    # -------------------------------------------------------------------------
    # AC5: Manager rights - jsocr.config (read only)
    # -------------------------------------------------------------------------

    def test_manager_can_read_config(self):
        """Test that manager can read jsocr.config."""
        config_as_manager = self.config.with_user(self.test_manager)
        url = config_as_manager.ollama_url
        self.assertEqual(url, 'http://localhost:11434')

    def test_manager_cannot_write_config(self):
        """Test that manager cannot write jsocr.config."""
        config_as_manager = self.config.with_user(self.test_manager)
        with self.assertRaises(AccessError):
            config_as_manager.write({'ollama_url': 'http://other:11434'})

    # -------------------------------------------------------------------------
    # AC5: Manager rights - jsocr.import.job (full CRUD)
    # -------------------------------------------------------------------------

    def test_manager_can_read_job(self):
        """Test that manager can read jsocr.import.job."""
        job_as_manager = self.job.with_user(self.test_manager)
        filename = job_as_manager.pdf_filename
        self.assertEqual(filename, 'manager_test.pdf')

    def test_manager_can_write_job(self):
        """Test that manager can write jsocr.import.job."""
        job_as_manager = self.job.with_user(self.test_manager)
        job_as_manager.write({'state': 'processing'})
        self.assertEqual(job_as_manager.state, 'processing')

    def test_manager_can_create_job(self):
        """Test that manager can create jsocr.import.job."""
        JobModel = self.env['jsocr.import.job'].with_user(self.test_manager)
        job = JobModel.create({
            'pdf_filename': 'manager_created.pdf',
            'pdf_file': b'new',
            'state': 'pending',
        })
        self.assertTrue(job.id)

    def test_manager_can_unlink_job(self):
        """Test that manager can delete jsocr.import.job."""
        # Create a job to delete
        job_to_delete = self.env['jsocr.import.job'].create({
            'pdf_filename': 'delete.pdf',
            'pdf_file': b'delete',
            'state': 'pending',
        })
        job_as_manager = job_to_delete.with_user(self.test_manager)
        job_id = job_as_manager.id
        job_as_manager.unlink()
        self.assertFalse(self.env['jsocr.import.job'].search([('id', '=', job_id)]))

    # -------------------------------------------------------------------------
    # AC5: Manager rights - jsocr.mask (full CRUD)
    # -------------------------------------------------------------------------

    def test_manager_can_read_mask(self):
        """Test that manager can read jsocr.mask."""
        mask_as_manager = self.mask.with_user(self.test_manager)
        name = mask_as_manager.name
        self.assertEqual(name, 'Manager Test Mask')

    def test_manager_can_write_mask(self):
        """Test that manager can write jsocr.mask."""
        mask_as_manager = self.mask.with_user(self.test_manager)
        mask_as_manager.write({'mask_data': '{"version": 2}'})
        self.assertEqual(mask_as_manager.mask_data, '{"version": 2}')

    def test_manager_can_create_mask(self):
        """Test that manager can create jsocr.mask."""
        MaskModel = self.env['jsocr.mask'].with_user(self.test_manager)
        mask = MaskModel.create({
            'name': 'Manager Created Mask',
            'partner_id': self.partner.id,
            'mask_data': '{"version": 1, "fields": {"date": {}}}',
        })
        self.assertTrue(mask.id)

    def test_manager_can_unlink_mask(self):
        """Test that manager can delete jsocr.mask."""
        mask_to_delete = self.env['jsocr.mask'].create({
            'name': 'Mask To Delete',
            'partner_id': self.partner.id,
            'mask_data': '{}',
        })
        mask_as_manager = mask_to_delete.with_user(self.test_manager)
        mask_id = mask_as_manager.id
        mask_as_manager.unlink()
        self.assertFalse(self.env['jsocr.mask'].search([('id', '=', mask_id)]))

    # -------------------------------------------------------------------------
    # AC5: Manager rights - jsocr.correction (full CRUD)
    # -------------------------------------------------------------------------

    def test_manager_can_read_correction(self):
        """Test that manager can read jsocr.correction."""
        correction_as_manager = self.correction.with_user(self.test_manager)
        field_name = correction_as_manager.field_name
        self.assertEqual(field_name, 'supplier')

    def test_manager_can_write_correction(self):
        """Test that manager can write jsocr.correction."""
        correction_as_manager = self.correction.with_user(self.test_manager)
        correction_as_manager.write({'corrected_value': 'Manager Updated'})
        self.assertEqual(correction_as_manager.corrected_value, 'Manager Updated')

    def test_manager_can_create_correction(self):
        """Test that manager can create jsocr.correction."""
        CorrectionModel = self.env['jsocr.correction'].with_user(self.test_manager)
        correction = CorrectionModel.create({
            'import_job_id': self.job.id,
            'field_name': 'amount',
            'original_value': '100.00',
            'corrected_value': '150.00',
            'correction_type': 'field_value',
        })
        self.assertTrue(correction.id)

    def test_manager_can_unlink_correction(self):
        """Test that manager can delete jsocr.correction."""
        correction_to_delete = self.env['jsocr.correction'].create({
            'import_job_id': self.job.id,
            'field_name': 'delete_test',
            'original_value': 'old',
            'corrected_value': 'new',
            'correction_type': 'field_value',
        })
        correction_as_manager = correction_to_delete.with_user(self.test_manager)
        correction_id = correction_as_manager.id
        correction_as_manager.unlink()
        self.assertFalse(self.env['jsocr.correction'].search([('id', '=', correction_id)]))


@tagged('post_install', '-at_install', 'jsocr', 'jsocr_security')
class TestJsocrAdminRights(TransactionCase):
    """Test Admin group rights (AC6)."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures with a test admin."""
        super().setUpClass()
        cls.admin_group = cls.env.ref('js_invoice_ocr_ia.group_jsocr_admin')

        # Create a test admin with JSOCR Admin group
        cls.test_admin = cls.env['res.users'].create({
            'name': 'JSOCR Test Admin',
            'login': 'jsocr_test_admin',
            'email': 'jsocr_test_admin@example.com',
            'groups_id': [(6, 0, [
                cls.admin_group.id,
                cls.env.ref('base.group_user').id,  # Internal User
            ])],
        })

        # Create test records
        # jsocr.config is a singleton - no 'name' or 'ocr_engine' fields
        cls.config = cls.env['jsocr.config'].create({
            'ollama_url': 'http://localhost:11434',
        })

    # -------------------------------------------------------------------------
    # AC6: Admin rights - jsocr.config (full CRUD)
    # -------------------------------------------------------------------------

    def test_admin_can_read_config(self):
        """Test that admin can read jsocr.config."""
        config_as_admin = self.config.with_user(self.test_admin)
        url = config_as_admin.ollama_url
        self.assertEqual(url, 'http://localhost:11434')

    def test_admin_can_write_config(self):
        """Test that admin can write jsocr.config."""
        config_as_admin = self.config.with_user(self.test_admin)
        config_as_admin.write({'ollama_url': 'http://newhost:11434'})
        self.assertEqual(config_as_admin.ollama_url, 'http://newhost:11434')

    def test_admin_can_create_config(self):
        """Test that admin can create jsocr.config."""
        # Note: jsocr.config is singleton, but we test ACL permission
        # This will fail due to singleton constraint, but ACL should allow it
        ConfigModel = self.env['jsocr.config'].with_user(self.test_admin)
        # Delete existing config first to test create permission
        self.config.unlink()
        config = ConfigModel.create({
            'ollama_url': 'http://admin:11434',
        })
        self.assertTrue(config.id)

    def test_admin_can_unlink_config(self):
        """Test that admin can delete jsocr.config."""
        config_to_delete = self.env['jsocr.config'].create({
            'ollama_url': 'http://delete:11434',
        })
        config_as_admin = config_to_delete.with_user(self.test_admin)
        config_id = config_as_admin.id
        config_as_admin.unlink()
        self.assertFalse(self.env['jsocr.config'].search([('id', '=', config_id)]))

    def test_admin_is_only_group_with_config_write(self):
        """Test that only admin can write to jsocr.config."""
        # Get all ACL rules for jsocr.config with perm_write=1
        config_model = self.env['ir.model']._get('jsocr.config')
        write_rules = self.env['ir.model.access'].search([
            ('model_id', '=', config_model.id),
            ('perm_write', '=', True),
        ])
        # Only admin should have write permission
        groups_with_write = write_rules.mapped('group_id')
        self.assertEqual(len(groups_with_write), 1)
        self.assertEqual(groups_with_write, self.admin_group)


@tagged('post_install', '-at_install', 'jsocr', 'jsocr_security')
class TestJsocrInheritedRights(TransactionCase):
    """Test that group inheritance works correctly."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        super().setUpClass()
        cls.admin_group = cls.env.ref('js_invoice_ocr_ia.group_jsocr_admin')

        # Create a test admin
        cls.test_admin = cls.env['res.users'].create({
            'name': 'JSOCR Inherited Rights Test',
            'login': 'jsocr_inherited_test',
            'email': 'jsocr_inherited_test@example.com',
            'groups_id': [(6, 0, [
                cls.admin_group.id,
                cls.env.ref('base.group_user').id,
            ])],
        })

        # jsocr.import.job - 'name' is computed, use 'pdf_file' not 'pdf_content'
        cls.job = cls.env['jsocr.import.job'].create({
            'pdf_filename': 'inherited.pdf',
            'pdf_file': b'test',
            'state': 'pending',
        })

    def test_admin_inherits_manager_rights(self):
        """Test that admin can do what manager can do."""
        # Admin should be able to create jobs (manager right)
        JobModel = self.env['jsocr.import.job'].with_user(self.test_admin)
        job = JobModel.create({
            'pdf_filename': 'admin_inherited.pdf',
            'pdf_file': b'admin',
            'state': 'pending',
        })
        self.assertTrue(job.id)

    def test_admin_inherits_user_rights(self):
        """Test that admin can do what user can do."""
        # Admin should be able to read jobs (user right)
        job_as_admin = self.job.with_user(self.test_admin)
        filename = job_as_admin.pdf_filename
        self.assertEqual(filename, 'inherited.pdf')

    def test_admin_has_all_user_groups(self):
        """Test that admin user has user and manager groups."""
        user_group = self.env.ref('js_invoice_ocr_ia.group_jsocr_user')
        manager_group = self.env.ref('js_invoice_ocr_ia.group_jsocr_manager')

        # Admin should have all implied groups
        self.assertTrue(self.test_admin.has_group('js_invoice_ocr_ia.group_jsocr_admin'))
        self.assertTrue(self.test_admin.has_group('js_invoice_ocr_ia.group_jsocr_manager'))
        self.assertTrue(self.test_admin.has_group('js_invoice_ocr_ia.group_jsocr_user'))
