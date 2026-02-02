# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

{
    'name': 'Invoice OCR IA',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Automated supplier invoice entry with OCR and AI',
    'description': """
Invoice OCR IA
==============
Addon Odoo 18 Community pour automatiser la saisie des factures fournisseurs
via OCR (Tesseract) et IA (Ollama local).

Features
--------
* Surveillance dossier pour nouveaux PDFs
* Extraction texte via PyMuPDF et Tesseract
* Analyse IA via Ollama local
* Création automatique de factures brouillon
* Indices de confiance par champ
* Apprentissage des corrections utilisateur

Multilingue
-----------
Support natif français, allemand et anglais (contexte suisse).
    """,
    'author': 'Joel Scheuner',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'queue_job',
    ],
    'external_dependencies': {
        'python': [
            'pymupdf',
            'pytesseract',
            'Pillow',
            'requests',
        ],
    },
    'data': [
        # Security (Story 1.7)
        'security/jsocr_security.xml',
        'security/ir.model.access.csv',

        # Views (Story 2.1+)
        'views/jsocr_config_views.xml',
        'views/menu.xml',

        # Data - will be added in Epic 3+
        # 'data/jsocr_cron.xml',
    ],
    'demo': [
        # Demo data - optional
        # 'demo/jsocr_demo.xml',
    ],
    'assets': {
        # Frontend assets - will be added in Epic 5
        # 'web.assets_backend': [
        #     'js_invoice_ocr_ia/static/src/components/**/*',
        #     'js_invoice_ocr_ia/static/src/scss/**/*',
        # ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
