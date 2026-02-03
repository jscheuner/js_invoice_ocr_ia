# Story 4.5: Extraction Lignes de Facture

Status: done

## Story

As a **systeme**,
I want **extraire les lignes de produits/services**,
So that **les lignes de facture soient pre-remplies** (FR15).

## Acceptance Criteria

1. **AC1: Extraction lignes**
   - **Given** une reponse JSON de l'IA
   - **When** le systeme parse la reponse
   - **Then** chaque ligne contient: description, quantity, unit_price, amount

2. **AC2: Stockage JSON**
   - **Given** des lignes extraites
   - **When** l'extraction est terminee
   - **Then** les lignes sont stockees dans le job (JSON)
   - **And** le format est un tableau d'objets

3. **AC3: Parsing montants**
   - **Given** des montants dans differents formats
   - **When** le systeme parse les lignes
   - **Then** les montants sont parses correctement (virgule/point decimal)
   - **And** les apostrophes comme separateurs de milliers sont geres

4. **AC4: Calcul automatique**
   - **Given** une ligne sans amount mais avec quantity et unit_price
   - **When** le systeme parse la ligne
   - **Then** amount est calcule automatiquement (quantity * unit_price)

## Tasks / Subtasks

- [x] **Task 1: Parser les lignes** (AC: #1, #2)
  - [x] Methode `parse_invoice_lines(lines_data)`
  - [x] Validation de chaque ligne
  - [x] Conversion en format standard

- [x] **Task 2: Parser les montants** (AC: #3)
  - [x] Methode `_parse_amount(value)`
  - [x] Support virgule/point decimal
  - [x] Support apostrophe comme separateur milliers

- [x] **Task 3: Calcul automatique** (AC: #4)
  - [x] Si amount manquant, calculer depuis qty * price
  - [x] Valeurs par defaut sensees

- [x] **Task 4: Stocker les lignes** (AC: #2)
  - [x] Champ extracted_lines (Text JSON)
  - [x] Serialisation JSON propre

## Dev Notes

### Line Structure
```json
{
  "description": "Service description",
  "quantity": 1.0,
  "unit_price": 100.00,
  "amount": 100.00
}
```

### Technical Requirements
- Description par defaut si vide: "Ligne facture"
- Quantite par defaut: 1.0
- Prix et amount peuvent etre 0

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- parse_invoice_lines validates and normalizes lines
- Amount calculation when missing
- Swiss format support (1'234,56)
- JSON storage in extracted_lines

### File List

**Files modified:**
- `js_invoice_ocr_ia/services/ai_service.py` - parse_invoice_lines, _parse_amount
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - extracted_lines field
- `js_invoice_ocr_ia/tests/test_ai_service.py` - Lines parsing tests

## Change Log
- **2026-02-02**: Story implemented as part of Epic 4 batch
