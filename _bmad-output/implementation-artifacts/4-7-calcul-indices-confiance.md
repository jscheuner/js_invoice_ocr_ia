# Story 4.7: Calcul Indices de Confiance

Status: done

## Story

As a **systeme**,
I want **calculer un indice de confiance pour chaque champ extrait**,
So that **l'utilisateur sache quels champs verifier** (FR17).

## Acceptance Criteria

1. **AC1: Score par champ**
   - **Given** une extraction IA terminee
   - **When** le systeme calcule les indices
   - **Then** chaque champ a un score 0-100%

2. **AC2: Criteres de scoring**
   - **Given** les donnees extraites
   - **When** le score est calcule
   - **Then** le score depend de: presence du champ, coherence des donnees, format valide

3. **AC3: Stockage JSON**
   - **Given** des indices calcules
   - **When** le calcul est termine
   - **Then** les indices sont stockes en JSON dans confidence_data
   - **And** le format suit le schema defini

4. **AC4: Indice global**
   - **Given** des indices par champ
   - **When** le systeme calcule l'indice global
   - **Then** un indice global est calcule (moyenne ponderee)
   - **And** les poids sont: supplier 15%, date 10%, lines 25%, amounts 40%

## Tasks / Subtasks

- [x] **Task 1: Calculer score par champ** (AC: #1, #2)
  - [x] Methode `_calculate_confidence(data)`
  - [x] Score fournisseur (presence, longueur)
  - [x] Score date (format valide, date raisonnable)
  - [x] Score lignes (lignes valides / total)
  - [x] Score montants (coherence HT+TVA=TTC)

- [x] **Task 2: Calculer indice global** (AC: #4)
  - [x] Moyenne ponderee des scores
  - [x] Poids configures selon importance

- [x] **Task 3: Stocker en JSON** (AC: #3)
  - [x] Format: {"field": {"value": x, "confidence": y}}
  - [x] Champ global inclus
  - [x] Stockage dans job.confidence_data

- [x] **Task 4: Tests** (AC: #1-#4)
  - [x] Test tous champs presents
  - [x] Test champs manquants
  - [x] Test coherence montants
  - [x] Test incoherence montants

## Dev Notes

### Confidence Schema
```json
{
  "supplier": {"value": "Muller SA", "confidence": 85},
  "date": {"value": "2026-01-15", "confidence": 95},
  "invoice_number": {"value": "INV-001", "confidence": 90},
  "lines": {"value": 3, "confidence": 80},
  "amount_untaxed": {"value": 100.0, "confidence": 90},
  "amount_tax": {"value": 7.7, "confidence": 90},
  "amount_total": {"value": 107.7, "confidence": 90},
  "global": {"value": 87, "confidence": 87}
}
```

### Weighting
- supplier: 15%
- date: 10%
- invoice_number: 10%
- lines: 25%
- amount_untaxed: 15%
- amount_tax: 10%
- amount_total: 15%

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- _calculate_confidence computes per-field scores
- Weighted average for global score
- Coherence check affects amount scores
- JSON format matches architecture spec

### File List

**Files modified:**
- `js_invoice_ocr_ia/services/ai_service.py` - _calculate_confidence and helpers
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - confidence_data field
- `js_invoice_ocr_ia/tests/test_ai_service.py` - Confidence tests

## Change Log
- **2026-02-02**: Story implemented as part of Epic 4 batch
