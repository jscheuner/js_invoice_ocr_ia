# Story 4.8: Creation Facture Brouillon

Status: done

## Story

As a **systeme**,
I want **creer une facture fournisseur brouillon dans Odoo**,
So that **l'utilisateur puisse valider et completer** (FR18).

## Acceptance Criteria

1. **AC1: Creation facture**
   - **Given** un job avec donnees extraites completes
   - **When** le systeme cree la facture
   - **Then** une account.move de type 'in_invoice' est creee en etat 'draft'

2. **AC2: Association fournisseur**
   - **Given** un fournisseur detecte
   - **When** la facture est creee
   - **Then** le partner_id est associe si trouve (FR19)

3. **AC3: Remplissage champs**
   - **Given** des donnees extraites
   - **When** la facture est creee
   - **Then** la date et reference fournisseur sont remplies
   - **And** le lien vers le job d'import est etabli

4. **AC4: Performance**
   - **Given** une creation de facture
   - **When** le processus s'execute
   - **Then** la creation prend < 5 secondes (NFR4)

## Tasks / Subtasks

- [x] **Task 1: Creer la facture** (AC: #1)
  - [x] Methode `_create_draft_invoice()`
  - [x] Type: in_invoice (facture fournisseur)
  - [x] Etat: draft

- [x] **Task 2: Remplir les champs** (AC: #2, #3)
  - [x] partner_id si detecte
  - [x] invoice_date depuis extraction
  - [x] ref depuis invoice_number
  - [x] jsocr_import_job_id pour le lien

- [x] **Task 3: Lier au job** (AC: #3)
  - [x] Stocker invoice_id dans le job
  - [x] Copier confidence_data sur la facture

- [x] **Task 4: Bouton action** (AC: #1)
  - [x] Methode `action_create_invoice()`
  - [x] Retourne action pour ouvrir la facture

## Dev Notes

### Invoice Fields Mapping
- partner_id <- job.partner_id
- invoice_date <- job.extracted_invoice_date
- ref <- job.extracted_invoice_number
- jsocr_import_job_id <- job.id
- jsocr_confidence_data <- job.confidence_data

### Technical Requirements
- Utiliser create() standard Odoo
- Ne pas valider automatiquement (rester en draft)
- Performance < 5s (NFR4)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- _create_draft_invoice creates in_invoice in draft state
- Partner and dates populated from extracted data
- Invoice linked back to job
- Confidence data copied to invoice

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - _create_draft_invoice, action_create_invoice
- `js_invoice_ocr_ia/views/jsocr_import_job_views.xml` - Create invoice button

## Change Log
- **2026-02-02**: Story implemented as part of Epic 4 batch
