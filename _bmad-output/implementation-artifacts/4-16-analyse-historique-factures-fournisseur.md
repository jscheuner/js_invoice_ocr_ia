# Story 4.16: Analyse Historique Factures Fournisseur

Status: done

## Story

As a **systeme**,
I want **analyser les 10 dernieres factures validees d'un fournisseur**,
So that **je puisse predire les comptes de charge appropries pour les nouvelles factures**.

## Acceptance Criteria

1. **AC1: Recuperation historique**
   - **Given** un fournisseur identifie pour une nouvelle facture
   - **When** le systeme prepare la creation des lignes de facture
   - **Then** les 10 dernieres factures validees (etat 'posted') du fournisseur sont recuperees

2. **AC2: Extraction des lignes**
   - **Given** les factures historiques recuperees
   - **When** le systeme analyse l'historique
   - **Then** toutes les lignes de ces factures sont extraites avec leur description et compte de charge

3. **AC3: Filtrage comptes**
   - **Given** les lignes extraites
   - **When** le systeme structure les donnees
   - **Then** seuls les comptes de type 'expense' sont consideres

4. **AC4: Historique insuffisant**
   - **Given** un fournisseur avec moins de 10 factures
   - **When** le systeme recupere l'historique
   - **Then** toutes les factures disponibles sont utilisees

## Tasks / Subtasks

- [x] **Task 1: Methode recuperation historique** (AC: #1, #4)
  - [x] `_get_supplier_invoice_history(partner_id, limit=10)`
  - [x] Filtrer sur state='posted' et move_type='in_invoice'
  - [x] Ordonner par date decroissante

- [x] **Task 2: Extraction lignes avec comptes** (AC: #2, #3)
  - [x] `_get_historical_lines_data(invoices)`
  - [x] Extraire description, account_id pour chaque ligne
  - [x] Filtrer les comptes de type expense

## Dev Notes

### Technical Implementation
- Methode sur jsocr.import.job
- Retourne liste de dicts {description, account_id, account_code}
- Normalisation des descriptions (lowercase, sans accents)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- _get_supplier_invoice_history fetches last 10 posted invoices
- _get_historical_lines_data extracts line descriptions and accounts
- Descriptions normalized for matching

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - Added history analysis methods

## Change Log
- **2026-02-03**: Story implemented
