# Story 4.18: Stockage Patterns Compte par Fournisseur

Status: done

## Story

As a **systeme**,
I want **memoriser les associations description/compte apprises**,
So that **les predictions s'ameliorent avec le temps sans recalcul**.

## Acceptance Criteria

1. **AC1: Modele jsocr.account.pattern**
   - **Given** le systeme apprend des factures
   - **When** un pattern est cree
   - **Then** le modele stocke: partner_id, keywords, account_id, usage_count, last_used

2. **AC2: Mise a jour patterns**
   - **Given** une facture validee avec des lignes
   - **When** la facture passe en etat 'posted'
   - **Then** pour chaque ligne, l'association est enregistree ou mise a jour

3. **AC3: Usage count**
   - **Given** un pattern existant utilise
   - **When** le pattern est reutilise
   - **Then** usage_count est incremente

4. **AC4: Priorite patterns**
   - **Given** des patterns existants
   - **When** le systeme predit un compte
   - **Then** les patterns sont utilises en priorite avant l'analyse historique

## Tasks / Subtasks

- [x] **Task 1: Creer modele jsocr.account.pattern** (AC: #1)
  - [x] Champs: partner_id, keywords, account_id, usage_count, last_used
  - [x] Contrainte unique sur (partner_id, keywords)
  - [x] Index sur partner_id

- [x] **Task 2: Methode mise a jour patterns** (AC: #2, #3)
  - [x] `_update_account_pattern(partner_id, description, account_id)`
  - [x] Creer ou incrementer usage_count

- [x] **Task 3: Integration dans prediction** (AC: #4)
  - [x] `_get_pattern_account(partner_id, description)`
  - [x] Recherche pattern existant
  - [x] Retourne account_id si trouve avec haute confiance

## Dev Notes

### Model Structure
```python
class JsocrAccountPattern(models.Model):
    _name = 'jsocr.account.pattern'
    partner_id = Many2one('res.partner')
    keywords = Char()  # normalized description keywords
    account_id = Many2one('account.account')
    usage_count = Integer(default=1)
    last_used = Datetime()
```

### Pattern Lookup Priority
1. Exact keyword match with high usage_count
2. Partial keyword match
3. Fall back to historical analysis

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- Created jsocr.account.pattern model
- Added to __init__.py and __manifest__.py
- Pattern lookup integrated into prediction flow
- Security rules added for pattern model

### File List

**Files created:**
- `js_invoice_ocr_ia/models/jsocr_account_pattern.py` - New model

**Files modified:**
- `js_invoice_ocr_ia/models/__init__.py` - Import new model
- `js_invoice_ocr_ia/__manifest__.py` - Add security file
- `js_invoice_ocr_ia/security/ir.model.access.csv` - ACL for pattern model
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - Pattern integration

## Change Log
- **2026-02-03**: Story implemented
