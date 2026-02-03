# Story 4.9: Pre-remplissage Lignes Facture

Status: done

## Story

As a **systeme**,
I want **pre-remplir les lignes de la facture brouillon**,
So that **l'utilisateur n'ait pas a saisir manuellement** (FR20).

## Acceptance Criteria

1. **AC1: Creation lignes**
   - **Given** une facture brouillon creee
   - **When** les lignes sont ajoutees
   - **Then** chaque ligne extraite devient une account.move.line

2. **AC2: Compte de charge fournisseur**
   - **Given** un fournisseur avec compte par defaut configure
   - **When** les lignes sont creees
   - **Then** le compte de charge par defaut du fournisseur est utilise

3. **AC3: Compte de charge generique**
   - **Given** un fournisseur sans compte par defaut
   - **When** les lignes sont creees
   - **Then** un compte de charge generique est utilise (6xxx)

4. **AC4: Donnees des lignes**
   - **Given** des lignes extraites
   - **When** les lignes facture sont creees
   - **Then** les quantites et prix unitaires sont remplis
   - **And** la description est copiee

## Tasks / Subtasks

- [x] **Task 1: Creer les lignes** (AC: #1)
  - [x] Methode `_create_invoice_lines(invoice)`
  - [x] Parser extracted_lines JSON
  - [x] Creer account.move.line pour chaque ligne

- [x] **Task 2: Determiner le compte** (AC: #2, #3)
  - [x] Methode `_get_expense_account()`
  - [x] Priorite: fournisseur > generique 6xxx > expense type
  - [x] Gerer le cas sans compte trouve

- [x] **Task 3: Remplir les donnees** (AC: #4)
  - [x] name = description
  - [x] quantity = quantity
  - [x] price_unit = unit_price
  - [x] account_id = compte determine

## Dev Notes

### Account Selection Priority
1. partner.jsocr_default_account_id
2. Compte commencant par 6 (charges suisses)
3. Compte de type 'expense'

### Technical Requirements
- Les lignes sont creees en mode brouillon
- Pas de calcul TVA automatique (sera fait par Odoo)
- Gestion cas sans lignes extraites

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- _create_invoice_lines creates lines from JSON
- _get_expense_account follows priority order
- Lines include description, quantity, price_unit
- Handles missing lines gracefully

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - _create_invoice_lines, _get_expense_account

## Change Log
- **2026-02-02**: Story implemented as part of Epic 4 batch
