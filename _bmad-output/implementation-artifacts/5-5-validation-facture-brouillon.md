# Story 5.5: Validation Facture Brouillon

Status: done

## Story

As a **utilisateur OCR**,
I want **valider une facture brouillon pour la comptabiliser**,
So that **la facture soit enregistree officiellement** (FR24).

## Acceptance Criteria

1. **AC1: Bouton confirmer**
   - **Given** une facture brouillon complete et verifiee
   - **When** je clique sur "Confirmer"
   - **Then** la facture passe en etat "posted"

2. **AC2: Ecritures comptables**
   - **Given** une facture confirmee
   - **When** la validation est terminee
   - **Then** les ecritures comptables sont generees

3. **AC3: Job conserve**
   - **Given** une facture OCR validee
   - **When** la validation est terminee
   - **Then** le job d'import associe reste en etat "done"

4. **AC4: Apprentissage**
   - **Given** une facture OCR validee
   - **When** la facture passe en posted
   - **Then** les patterns de compte sont appris (Story 4.20)

## Tasks / Subtasks

- [x] **Task 1: Validation native Odoo** (AC: #1, #2)
  - [x] Le bouton "Confirmer" standard Odoo fonctionne
  - [x] action_post() est surcharge pour l'apprentissage

- [x] **Task 2: Apprentissage a la validation** (AC: #4)
  - [x] action_post() override deja implemente (Story 4.20)
  - [x] _learn_account_corrections() appele automatiquement

## Dev Notes

La validation est le bouton standard Odoo "Confirmer" qui appelle action_post().
L'override de action_post() (Story 4.20) gere automatiquement l'apprentissage.

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes
- Standard Odoo Confirm button triggers action_post()
- action_post() override (Story 4.20) handles pattern learning
- No additional code needed

### File List
No files modified - leverages Story 4.20 override.

## Change Log
- **2026-02-04**: Story validated (native Odoo + Story 4.20)
