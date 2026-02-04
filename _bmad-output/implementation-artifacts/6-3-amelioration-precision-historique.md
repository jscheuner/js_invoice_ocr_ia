# Story 6.3: Amelioration Precision par Historique

Status: done

## Story

As a **systeme**,
I want **ameliorer la precision des predictions en enrichissant les patterns a chaque validation**,
So that **les futures factures du meme fournisseur soient mieux predites**.

## Acceptance Criteria

1. **AC1: Mise a jour patterns a la validation**
   - **Given** une facture OCR validee avec des lignes de charge
   - **When** la facture est postee
   - **Then** les patterns jsocr.account.pattern sont crees ou mis a jour pour chaque ligne

2. **AC2: Detection corrections compte ligne**
   - **Given** une ligne avec un compte predit different du compte final
   - **When** la facture est validee
   - **Then** une correction de type 'line_account' est enregistree

3. **AC3: Enrichissement continu**
   - **Given** un pattern existant pour un fournisseur et des mots-cles
   - **When** une nouvelle facture confirme le meme mapping
   - **Then** le usage_count du pattern est incremente

## Tasks / Subtasks

- [x] **Task 1: Hook _learn_account_corrections** (AC: #1, #2)
  - [x] Appeler depuis action_post pour chaque facture OCR
  - [x] Parcourir les lignes de charge

- [x] **Task 2: Creation/mise a jour patterns** (AC: #1, #3)
  - [x] Appeler PatternModel.get_or_create_pattern() pour chaque ligne
  - [x] Incrementer usage_count si pattern existe

- [x] **Task 3: Enregistrement corrections** (AC: #2)
  - [x] Comparer jsocr_predicted_account_id avec account_id final
  - [x] Creer jsocr.correction si different

## Dev Notes

### Technical Implementation
- _learn_account_corrections() sur account.move (Story 4.20 integration)
- Utilise jsocr.account.pattern.get_or_create_pattern()
- Detecte les corrections via jsocr_predicted_account_id

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- Les patterns sont enrichis a chaque validation de facture
- Les corrections de compte sont tracees pour apprentissage
- Integration avec le pipeline de prediction Stories 4.16-4.20

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/account_move.py` - Added _learn_account_corrections()

## Change Log
- **2026-02-04**: Story implemented
