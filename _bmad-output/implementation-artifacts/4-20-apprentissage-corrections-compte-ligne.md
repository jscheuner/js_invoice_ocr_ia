# Story 4.20: Apprentissage des Corrections de Compte par Ligne

Status: done

## Story

As a **systeme**,
I want **apprendre quand l'utilisateur corrige le compte d'une ligne**,
So that **les prochaines predictions soient plus precises**.

## Acceptance Criteria

1. **AC1: Detection correction**
   - **Given** une facture brouillon ou l'utilisateur modifie le compte d'une ligne
   - **When** la facture est validee
   - **Then** si le compte final differe du compte predit, une correction est enregistree

2. **AC2: Creation jsocr.correction**
   - **Given** une correction detectee
   - **When** le systeme enregistre
   - **Then** une jsocr.correction est creee avec type 'line_account'

3. **AC3: Mise a jour pattern**
   - **Given** une correction enregistree
   - **When** le pattern est mis a jour
   - **Then** le nouveau pattern est cree ou usage_count incremente

4. **AC4: Priorite patterns corriges**
   - **Given** un pattern corrige 3+ fois
   - **When** le systeme predit un compte
   - **Then** ce pattern devient prioritaire

## Tasks / Subtasks

- [x] **Task 1: Hook validation facture** (AC: #1)
  - [x] Surcharger write() sur account.move
  - [x] Detecter passage draft -> posted
  - [x] Comparer comptes predits vs finaux

- [x] **Task 2: Enregistrement correction** (AC: #2)
  - [x] Creer jsocr.correction avec type='line_account'
  - [x] Stocker original_value (account predit) et corrected_value (account final)

- [x] **Task 3: Update pattern** (AC: #3, #4)
  - [x] Appeler _update_account_pattern
  - [x] Pattern avec usage_count >= 3 a priorite

## Dev Notes

### Correction Type
New correction_type value: 'line_account'
- field_name = 'account_id'
- original_value = predicted account code
- corrected_value = final account code

### Pattern Priority
Patterns with usage_count >= 3 are considered "confirmed"
and get a confidence boost of +20%

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- Added write override on account.move to detect validations
- Creates correction records for changed accounts
- Updates patterns when corrections are made
- Patterns with high usage get priority

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/account_move.py` - write() override for learning
- `js_invoice_ocr_ia/models/jsocr_account_pattern.py` - Priority logic

## Change Log
- **2026-02-03**: Story implemented
