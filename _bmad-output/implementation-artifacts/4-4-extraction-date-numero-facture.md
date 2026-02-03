# Story 4.4: Extraction Date et Numero Facture

Status: done

## Story

As a **systeme**,
I want **extraire la date et le numero de facture**,
So that **les champs obligatoires soient pre-remplis** (FR13, FR14).

## Acceptance Criteria

1. **AC1: Extraction date**
   - **Given** une reponse JSON de l'IA
   - **When** le systeme parse la reponse
   - **Then** invoice_date est extrait et converti en date Odoo (YYYY-MM-DD)

2. **AC2: Formats de date supportes**
   - **Given** differents formats de date
   - **When** le systeme parse la date
   - **Then** les formats FR/DE/EN sont supportes (DD.MM.YYYY, DD/MM/YYYY, YYYY-MM-DD)
   - **And** les annees courtes (YY) sont converties en annees completes

3. **AC3: Extraction numero facture**
   - **Given** une reponse JSON de l'IA
   - **When** le systeme parse la reponse
   - **Then** invoice_number est extrait (reference fournisseur)
   - **And** la valeur est stockee dans extracted_invoice_number

4. **AC4: Stockage des valeurs**
   - **Given** des valeurs extraites
   - **When** l'extraction est terminee
   - **Then** les valeurs sont stockees dans le job
   - **And** les valeurs null sont gerees proprement

## Tasks / Subtasks

- [x] **Task 1: Parser la date** (AC: #1, #2)
  - [x] Methode `parse_invoice_date(date_str)`
  - [x] Support format ISO (YYYY-MM-DD)
  - [x] Support format europeen (DD.MM.YYYY, DD/MM/YYYY)
  - [x] Support annees courtes (DD.MM.YY)

- [x] **Task 2: Parser le numero facture** (AC: #3)
  - [x] Extraction directe du champ invoice_number
  - [x] Nettoyage des espaces
  - [x] Gestion des valeurs null

- [x] **Task 3: Stocker les valeurs** (AC: #4)
  - [x] Champ extracted_invoice_date (Date)
  - [x] Champ extracted_invoice_number (Char)
  - [x] Integration dans _store_extracted_data

- [x] **Task 4: Tests** (AC: #1-#4)
  - [x] Test format ISO
  - [x] Test format europeen point
  - [x] Test format europeen slash
  - [x] Test annee courte
  - [x] Test date invalide

## Dev Notes

### Date Format Handling
- ISO (YYYY-MM-DD): Retourne tel quel
- Europeen (DD.MM.YYYY ou DD/MM/YYYY): Converti en ISO
- Court (DD.MM.YY): Prefix 20 pour l'annee

### Technical Requirements
- La date doit etre au format Odoo (YYYY-MM-DD)
- Le numero de facture devient la reference fournisseur (ref)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- parse_invoice_date handles multiple formats
- Automatic conversion to ISO format
- Invoice number stored directly
- Full test coverage

### File List

**Files modified:**
- `js_invoice_ocr_ia/services/ai_service.py` - parse_invoice_date method
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - extracted fields
- `js_invoice_ocr_ia/tests/test_ai_service.py` - Date parsing tests

## Change Log
- **2026-02-02**: Story implemented as part of Epic 4 batch
