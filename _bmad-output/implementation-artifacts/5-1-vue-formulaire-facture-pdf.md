# Story 5.1: Vue Formulaire Facture avec PDF

Status: done

## Story

As a **utilisateur OCR**,
I want **voir la facture brouillon avec le PDF source a cote**,
So that **je puisse verifier les donnees extraites**.

## Acceptance Criteria

1. **AC1: Onglet PDF source**
   - **Given** je suis sur une facture brouillon creee par OCR
   - **When** j'ouvre le formulaire
   - **Then** un onglet "PDF Source OCR" est visible avec le PDF integre

2. **AC2: PDF viewer**
   - **Given** l'onglet PDF est ouvert
   - **When** je consulte le PDF
   - **Then** je peux voir le PDF via le widget pdf_viewer natif Odoo

3. **AC3: Info job OCR**
   - **Given** une facture OCR
   - **When** j'ouvre l'onglet PDF
   - **Then** je vois le lien vers le job d'import et la confiance globale

4. **AC4: Visibilite conditionnelle**
   - **Given** une facture NON creee par OCR
   - **When** j'ouvre le formulaire
   - **Then** l'onglet PDF Source OCR n'est PAS visible

## Tasks / Subtasks

- [x] **Task 1: Vue heritee account.move** (AC: #1, #4)
  - [x] Creer account_move_views.xml
  - [x] Heriter de account.view_move_form
  - [x] Onglet conditionnel sur jsocr_import_job_id

- [x] **Task 2: Widget PDF** (AC: #2)
  - [x] Utiliser widget="pdf_viewer" sur jsocr_source_pdf
  - [x] Style height: 800px

- [x] **Task 3: Info confiance** (AC: #3)
  - [x] Lien vers jsocr_import_job_id
  - [x] Widget progressbar pour jsocr_global_confidence

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### File List

**Files created:**
- `js_invoice_ocr_ia/views/account_move_views.xml`

**Files modified:**
- `js_invoice_ocr_ia/__manifest__.py` - Added view file

## Change Log
- **2026-02-04**: Story implemented
