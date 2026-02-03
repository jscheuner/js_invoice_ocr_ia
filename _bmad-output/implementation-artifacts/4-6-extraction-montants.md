# Story 4.6: Extraction Montants

Status: done

## Story

As a **systeme**,
I want **extraire les montants HT, TVA et TTC**,
So that **les totaux soient verifiables** (FR16).

## Acceptance Criteria

1. **AC1: Extraction montants**
   - **Given** une reponse JSON de l'IA
   - **When** le systeme parse la reponse
   - **Then** amount_untaxed, amount_tax, amount_total sont extraits

2. **AC2: Conversion float**
   - **Given** des montants en differents formats
   - **When** le systeme parse les montants
   - **Then** les montants sont convertis en float
   - **And** les formats suisses sont supportes (1'234.56)

3. **AC3: Verification coherence**
   - **Given** des montants extraits
   - **When** le systeme verifie la coherence
   - **Then** une verification est effectuee (HT + TVA approx TTC)
   - **And** un warning est loggue si incoherence > 1%

4. **AC4: Stockage des valeurs**
   - **Given** des montants extraits
   - **When** l'extraction est terminee
   - **Then** les montants sont stockes dans le job
   - **And** les valeurs null deviennent 0.0

## Tasks / Subtasks

- [x] **Task 1: Extraire les montants** (AC: #1, #2)
  - [x] Parser amount_untaxed, amount_tax, amount_total
  - [x] Utiliser _parse_amount pour conversion
  - [x] Gerer les valeurs null

- [x] **Task 2: Verifier la coherence** (AC: #3)
  - [x] Calculer HT + TVA
  - [x] Comparer avec TTC
  - [x] Logger warning si difference > 1%

- [x] **Task 3: Stocker les valeurs** (AC: #4)
  - [x] Champs Float avec digits='Account'
  - [x] Valeur 0.0 si null

## Dev Notes

### Coherence Check
- Tolerance: 1%
- Formule: abs(untaxed + tax - total) / total * 100
- Log warning sans montants precis (NFR8)

### Swiss VAT Rates
- Standard: 7.7%
- Reduit: 2.5%
- Exempt: 0%

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- _parse_amount handles all Swiss formats
- Coherence check with 1% tolerance
- Warning logged for incoherent amounts (without values)
- Fields stored as Float with Account precision

### File List

**Files modified:**
- `js_invoice_ocr_ia/services/ai_service.py` - _calculate_amounts_confidence
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - Amount fields
- `js_invoice_ocr_ia/tests/test_ai_service.py` - Amount tests

## Change Log
- **2026-02-02**: Story implemented as part of Epic 4 batch
