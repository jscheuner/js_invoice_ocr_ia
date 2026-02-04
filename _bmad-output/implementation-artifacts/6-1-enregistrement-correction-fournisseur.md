# Story 6.1: Enregistrement Correction Fournisseur

Status: done

## Story

As a **systeme**,
I want **detecter quand l'utilisateur corrige le fournisseur d'une facture OCR**,
So that **je puisse ajouter le nom detecte par l'IA comme alias du bon fournisseur**.

## Acceptance Criteria

1. **AC1: Detection correction fournisseur**
   - **Given** une facture OCR en brouillon avec un fournisseur detecte par l'IA
   - **When** l'utilisateur change le fournisseur et valide la facture
   - **Then** le systeme detecte que le fournisseur a ete modifie

2. **AC2: Ajout alias fournisseur**
   - **Given** une correction de fournisseur detectee
   - **When** le systeme traite la correction
   - **Then** le nom detecte par l'IA est ajoute comme alias du fournisseur correct

3. **AC3: Enregistrement correction**
   - **Given** une correction de fournisseur detectee
   - **When** le systeme traite la correction
   - **Then** un enregistrement jsocr.correction de type 'supplier_alias' est cree

4. **AC4: Pas de doublon**
   - **Given** un fournisseur non modifie par l'utilisateur
   - **When** la facture est validee
   - **Then** aucune correction n'est enregistree

## Tasks / Subtasks

- [x] **Task 1: Hook action_post** (AC: #1)
  - [x] Override action_post sur account.move
  - [x] Appeler _learn_supplier_correction() pour chaque facture OCR

- [x] **Task 2: Detection correction** (AC: #1, #4)
  - [x] Comparer partner_id de la facture avec celui du job
  - [x] Ignorer si pas de changement

- [x] **Task 3: Ajout alias et correction** (AC: #2, #3)
  - [x] Appeler partner.add_alias(extracted_name)
  - [x] Creer jsocr.correction avec type 'supplier_alias'

## Dev Notes

### Technical Implementation
- Methode _learn_supplier_correction() sur account.move
- Utilise job.extracted_supplier_name et job.partner_id pour comparer
- Appel partner.add_alias() pour ajouter l'alias au JSON jsocr_aliases

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- Hook action_post detecte les corrections fournisseur a la validation
- L'alias est ajoute automatiquement au partenaire correct
- Un enregistrement jsocr.correction est cree pour tracabilite

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/account_move.py` - Added _learn_supplier_correction() and action_post override

## Change Log
- **2026-02-04**: Story implemented
