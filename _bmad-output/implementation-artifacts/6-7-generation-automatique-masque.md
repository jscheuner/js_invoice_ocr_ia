# Story 6.7: Generation Automatique Masque

Status: done

## Story

As a **systeme**,
I want **generer automatiquement un masque d'extraction apres 3 factures validees d'un meme fournisseur**,
So that **les patterns de facturation du fournisseur soient captures pour accelerer les traitements futurs**.

## Acceptance Criteria

1. **AC1: Declenchement apres 3 factures**
   - **Given** un fournisseur sans masque existant
   - **When** sa 3eme facture OCR est validee
   - **Then** un masque est automatiquement genere

2. **AC2: Contenu du masque genere**
   - **Given** le systeme genere un masque
   - **When** les 10 dernieres factures sont analysees
   - **Then** le masque contient: version, frequence reference fournisseur, nombre moyen de lignes, comptes les plus utilises

3. **AC3: Increment masque existant**
   - **Given** un fournisseur avec un masque actif existant
   - **When** une nouvelle facture OCR est validee
   - **Then** le usage_count du masque existant est incremente

4. **AC4: Masque auto-genere identifie**
   - **Given** un masque auto-genere
   - **When** on consulte ses donnees JSON
   - **Then** le champ auto_generated est a true avec le nombre de factures source

## Tasks / Subtasks

- [x] **Task 1: Trigger a la validation** (AC: #1, #3)
  - [x] _trigger_mask_generation() appele depuis action_post
  - [x] Verifier si masque existant -> incrementer
  - [x] Sinon compter les factures posted -> generer si >= 3

- [x] **Task 2: Generation masque** (AC: #2, #4)
  - [x] generate_mask_from_history(partner_id) sur jsocr.mask
  - [x] Analyser les 10 dernieres factures posted
  - [x] Calculer frequence ref fournisseur
  - [x] Calculer nombre moyen de lignes expense
  - [x] Capturer les 5 comptes les plus utilises

- [x] **Task 3: Creation masque** (AC: #4)
  - [x] Creer jsocr.mask avec nom 'Auto - {partner.name}'
  - [x] mask_data en JSON avec version, auto_generated, source_invoice_count, fields, common_accounts

## Dev Notes

### Technical Implementation
- _trigger_mask_generation() sur account.move
- generate_mask_from_history() sur jsocr.mask
- Masque cree avec prefix 'Auto -' pour identification
- Minimum 3 factures pour generer (configurable via code)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- Masque genere automatiquement apres 3 factures
- Contient statistiques sur les patterns de facturation
- Usage_count incremente pour masques existants
- Flag auto_generated dans le JSON

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/account_move.py` - Added _trigger_mask_generation()
- `js_invoice_ocr_ia/models/jsocr_mask.py` - Added generate_mask_from_history()

## Change Log
- **2026-02-04**: Story implemented
