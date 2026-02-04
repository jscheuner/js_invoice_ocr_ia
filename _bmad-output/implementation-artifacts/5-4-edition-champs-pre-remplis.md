# Story 5.4: Edition des Champs Pre-remplis

Status: done

## Story

As a **utilisateur OCR**,
I want **corriger les champs pre-remplis avant validation**,
So that **je puisse rectifier les erreurs d'extraction** (FR23).

## Acceptance Criteria

1. **AC1: Edition fournisseur**
   - **Given** une facture brouillon OCR
   - **When** je modifie le fournisseur
   - **Then** la modification est enregistree

2. **AC2: Edition lignes**
   - **Given** une facture brouillon OCR
   - **When** je modifie une ligne (description, quantite, prix, compte)
   - **Then** la modification est enregistree

3. **AC3: Ajout/suppression lignes**
   - **Given** une facture brouillon OCR
   - **When** j'ajoute ou supprime une ligne
   - **Then** le changement est pris en compte

## Tasks / Subtasks

- [x] **Task 1: Verification champs editables** (AC: #1, #2, #3)
  - [x] Facture brouillon en mode draft = editable par defaut dans Odoo
  - [x] Les champs partner_id, invoice_date, ref sont editables
  - [x] Les lignes sont editables (ajouter/modifier/supprimer)

## Dev Notes

Cette story est nativement supportee par Odoo. Les factures en etat 'draft'
sont editables. Aucun readonly n'est force sur les champs principaux dans
la vue heritee JSOCR. Les champs JSOCR (confidence, source, predicted)
sont en readonly car ce sont des metadonnees du systeme.

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes
- Standard Odoo draft invoice editing is fully supported
- No additional code needed - the inherited view preserves editability

### File List
No files modified - native Odoo behavior.

## Change Log
- **2026-02-04**: Story validated (native Odoo)
