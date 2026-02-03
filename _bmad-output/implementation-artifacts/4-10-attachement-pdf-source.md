# Story 4.10: Attachement PDF Source

Status: done

## Story

As a **systeme**,
I want **attacher le PDF source a la facture creee**,
So that **l'utilisateur puisse consulter l'original** (FR21).

## Acceptance Criteria

1. **AC1: Creation attachment**
   - **Given** une facture brouillon creee
   - **When** le PDF est attache
   - **Then** un ir.attachment est cree avec le PDF

2. **AC2: Lien a la facture**
   - **Given** un attachment cree
   - **When** il est lie
   - **Then** l'attachment est lie a la facture (res_model, res_id)

3. **AC3: Stockage dans champ facture**
   - **Given** un PDF source
   - **When** il est attache
   - **Then** le PDF est egalement stocke dans account.move.jsocr_source_pdf

4. **AC4: Metadata**
   - **Given** un attachment cree
   - **When** il est configure
   - **Then** le nom de fichier original est preserve
   - **And** le mimetype est application/pdf

## Tasks / Subtasks

- [x] **Task 1: Creer l'attachment** (AC: #1, #2, #4)
  - [x] Methode `_attach_pdf_to_invoice(invoice)`
  - [x] Creer ir.attachment avec datas
  - [x] Lier a la facture (res_model, res_id)
  - [x] Definir mimetype et nom

- [x] **Task 2: Stocker dans facture** (AC: #3)
  - [x] Copier pdf_file vers jsocr_source_pdf
  - [x] Copier pdf_filename vers jsocr_source_pdf_filename

- [x] **Task 3: Gerer cas sans PDF** (AC: #1)
  - [x] Verifier presence pdf_file
  - [x] Logger warning si absent

## Dev Notes

### Attachment Structure
- name: pdf_filename ou 'source.pdf'
- type: 'binary'
- datas: contenu PDF en base64
- res_model: 'account.move'
- res_id: invoice.id
- mimetype: 'application/pdf'

### Technical Requirements
- Le PDF reste accessible via le chatter
- Double stockage: attachment + champ binary
- Pas de suppression du PDF original

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- _attach_pdf_to_invoice creates ir.attachment
- PDF stored both as attachment and in jsocr_source_pdf
- Filename and mimetype properly set
- Handles missing PDF gracefully

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - _attach_pdf_to_invoice

## Change Log
- **2026-02-02**: Story implemented as part of Epic 4 batch
