# Story 6.2: Enregistrement Correction Compte de Charge

Status: done

## Story

As a **systeme**,
I want **detecter le compte de charge le plus utilise dans les lignes d'une facture OCR validee**,
So that **je puisse mettre a jour le compte de charge par defaut du fournisseur**.

## Acceptance Criteria

1. **AC1: Analyse comptes lignes**
   - **Given** une facture OCR validee avec des lignes de charge
   - **When** le systeme analyse les comptes
   - **Then** le compte de charge le plus utilise est identifie

2. **AC2: Mise a jour compte par defaut**
   - **Given** le compte le plus utilise est identifie
   - **When** il differe du compte par defaut actuel du fournisseur
   - **Then** le jsocr_default_account_id du fournisseur est mis a jour

3. **AC3: Enregistrement correction**
   - **Given** une mise a jour du compte par defaut
   - **When** le systeme traite la correction
   - **Then** un enregistrement jsocr.correction de type 'charge_account' est cree

4. **AC4: Filtrage comptes expense**
   - **Given** les lignes de la facture
   - **When** le systeme analyse les comptes
   - **Then** seuls les comptes de type expense sont consideres

## Tasks / Subtasks

- [x] **Task 1: Comptage comptes par ligne** (AC: #1, #4)
  - [x] Parcourir invoice_line_ids
  - [x] Filtrer par account_type expense
  - [x] Compter les occurrences de chaque account_id

- [x] **Task 2: Mise a jour compte par defaut** (AC: #2)
  - [x] Identifier le compte le plus utilise avec max()
  - [x] Comparer avec jsocr_default_account_id actuel
  - [x] Mettre a jour si different

- [x] **Task 3: Enregistrement correction** (AC: #3)
  - [x] Creer jsocr.correction avec type 'charge_account'
  - [x] Stocker ancien et nouveau code de compte

## Dev Notes

### Technical Implementation
- Methode _learn_charge_account_correction() sur account.move
- Compte les account_id de type expense dans les lignes
- Met a jour partner.jsocr_default_account_id si different

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- Le compte de charge par defaut est mis a jour automatiquement a la validation
- Seuls les comptes de type expense sont pris en compte
- Tracabilite via jsocr.correction

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/account_move.py` - Added _learn_charge_account_correction()

## Change Log
- **2026-02-04**: Story implemented
