# Story 6.6: Vue Gestion Masques

Status: done

## Story

As a **manager**,
I want **gerer les masques d'extraction et les patterns de compte appris**,
So that **je puisse superviser et ajuster l'apprentissage automatique du systeme**.

## Acceptance Criteria

1. **AC1: Vue liste masques**
   - **Given** un manager connecte
   - **When** il accede au menu Apprentissage > Masques d'extraction
   - **Then** une liste des masques est affichee avec nom, fournisseur, statut actif, utilisations et date

2. **AC2: Vue formulaire masque**
   - **Given** un manager clique sur un masque
   - **When** le formulaire s'ouvre
   - **Then** les details du masque sont affiches avec editeur JSON (ace widget)

3. **AC3: Filtres masques**
   - **Given** la vue liste des masques
   - **When** le manager utilise les filtres
   - **Then** il peut filtrer par actif/archive et regrouper par fournisseur

4. **AC4: Vue liste patterns de compte**
   - **Given** un manager connecte
   - **When** il accede au menu Apprentissage > Patterns de compte
   - **Then** une liste des patterns appris est affichee avec fournisseur, mots-cles, compte, utilisations

5. **AC5: Archive masque**
   - **Given** un manager sur le formulaire d'un masque
   - **When** il clique sur le bouton d'archivage
   - **Then** le masque est desactive

## Tasks / Subtasks

- [x] **Task 1: Vues masques** (AC: #1, #2, #3, #5)
  - [x] Creer jsocr_mask_view_list
  - [x] Creer jsocr_mask_view_form avec ace JSON editor
  - [x] Creer jsocr_mask_view_search avec filtres actif/archive
  - [x] Bouton toggle_active sur formulaire

- [x] **Task 2: Vues patterns** (AC: #4)
  - [x] Creer jsocr_account_pattern_view_list
  - [x] Creer jsocr_account_pattern_action

- [x] **Task 3: Actions et menus** (AC: #1, #4)
  - [x] Creer jsocr_mask_action
  - [x] Ajouter menu Masques d'extraction sous Apprentissage
  - [x] Ajouter menu Patterns de compte sous Apprentissage

## Dev Notes

### Technical Implementation
- Vues dans jsocr_mask_views.xml (masques + patterns)
- Ace widget pour edition JSON du mask_data
- Menu sous Apprentissage, visible pour group_jsocr_manager

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- Vue liste masques avec toggle actif
- Vue formulaire avec editeur JSON ace
- Vue liste patterns de compte
- Menus accessibles sous Apprentissage

### File List

**Files created:**
- `js_invoice_ocr_ia/views/jsocr_mask_views.xml` - Mask and pattern views

**Files modified:**
- `js_invoice_ocr_ia/views/menu.xml` - Added Masques and Patterns menu entries
- `js_invoice_ocr_ia/__manifest__.py` - Added jsocr_mask_views.xml to data list

## Change Log
- **2026-02-04**: Story implemented
