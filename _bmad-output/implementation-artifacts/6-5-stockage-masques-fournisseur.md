# Story 6.5: Stockage Masques par Fournisseur

Status: done

## Story

As a **systeme**,
I want **stocker et recuperer les masques d'extraction par fournisseur**,
So that **les futurs traitements puissent utiliser des masques optimises par fournisseur**.

## Acceptance Criteria

1. **AC1: Modele jsocr.mask existant**
   - **Given** le modele jsocr.mask deja cree en Epic 1
   - **When** le systeme a besoin d'un masque
   - **Then** il peut rechercher par partner_id et recuperer le masque le plus utilise

2. **AC2: Methode get_mask_for_partner**
   - **Given** un partner_id valide
   - **When** get_mask_for_partner est appele
   - **Then** le masque actif avec le plus grand usage_count est retourne

3. **AC3: Increment usage**
   - **Given** un masque utilise avec succes
   - **When** action_increment_usage est appele
   - **Then** le usage_count est incremente de 1

4. **AC4: Pas de masque**
   - **Given** un fournisseur sans masque
   - **When** get_mask_for_partner est appele
   - **Then** False est retourne

## Tasks / Subtasks

- [x] **Task 1: Validation methodes existantes** (AC: #1, #2, #4)
  - [x] Verifier get_mask_for_partner fonctionne correctement
  - [x] Recherche par partner_id, active=True, limit=1
  - [x] Retourne False si aucun masque

- [x] **Task 2: Increment usage** (AC: #3)
  - [x] Verifier action_increment_usage fonctionne
  - [x] Incremente usage_count de 1

## Dev Notes

### Technical Implementation
- Le modele jsocr.mask a ete cree en Epic 1 (Story 1.4)
- Les methodes get_mask_for_partner et action_increment_usage etaient deja implementees
- Cette story valide leur bon fonctionnement dans le contexte d'apprentissage

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- Methodes deja existantes depuis Epic 1
- get_mask_for_partner retourne le masque le plus utilise
- action_increment_usage incremente le compteur

### File List

**Files validated:**
- `js_invoice_ocr_ia/models/jsocr_mask.py` - Existing methods validated

## Change Log
- **2026-02-04**: Story validated (methods already exist from Epic 1)
