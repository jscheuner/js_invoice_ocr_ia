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
* Creation automatique de factures brouillon
* Indices de confiance par champ
* Apprentissage des corrections utilisateur

Multilingue
-----------
Support natif francais, allemand et anglais (contexte suisse).
    """,
    'author': 'Joel Scheuner',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'account',
        # 'queue_job',  # TODO: Uncomment in Epic 4 (async job processing)
    ],
    'external_dependencies': {
        'python': [
            'fitz',          # PyMuPDF for PDF text extraction (Story 3.1)
            'pytesseract',   # Tesseract OCR for scanned PDFs (Story 3.2)
            'PIL',           # Pillow for image processing (Story 3.2)
        ],
    },
    'data': [
        # Security (Story 1.7)
        'security/jsocr_security.xml',
        'security/ir.model.access.csv',

        # Views (Story 2.1+)
        'views/jsocr_config_views.xml',
        'views/jsocr_import_job_views.xml',
        'views/menu.xml',

        # Data (Story 3.4+)
        'data/jsocr_cron.xml',
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
    # 'post_init_hook': 'post_init_hook',  # TODO: Uncomment in Epic 4 (queue_job check)
}
