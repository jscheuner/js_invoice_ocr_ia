# Story 6.4: Vue Historique Corrections

Status: done

## Story

As a **manager**,
I want **consulter l'historique de toutes les corrections effectuees**,
So that **je puisse suivre l'apprentissage du systeme et identifier les problemes recurrents**.

## Acceptance Criteria

1. **AC1: Vue liste corrections**
   - **Given** un manager connecte
   - **When** il accede au menu Apprentissage > Historique Corrections
   - **Then** une liste de toutes les corrections est affichee avec job, champ, valeurs, type, utilisateur et date

2. **AC2: Vue formulaire correction**
   - **Given** un manager clique sur une correction
   - **When** le formulaire s'ouvre
   - **Then** les details complets de la correction sont affiches en lecture seule

3. **AC3: Filtres et regroupements**
   - **Given** la vue liste des corrections
   - **When** le manager utilise les filtres
   - **Then** il peut filtrer par type et regrouper par type, utilisateur, date ou job

4. **AC4: Menu accessible**
   - **Given** un manager connecte
   - **When** il navigue dans le menu OCR IA
   - **Then** le sous-menu Apprentissage > Historique Corrections est visible

## Tasks / Subtasks

- [x] **Task 1: Vue liste** (AC: #1)
  - [x] Creer jsocr_correction_view_list avec colonnes pertinentes
  - [x] Decoration couleur par type de correction

- [x] **Task 2: Vue formulaire** (AC: #2)
  - [x] Creer jsocr_correction_view_form en lecture seule
  - [x] Grouper les champs logiquement

- [x] **Task 3: Vue recherche** (AC: #3)
  - [x] Creer jsocr_correction_view_search
  - [x] Filtres par type de correction
  - [x] Regroupements par type, utilisateur, date, job

- [x] **Task 4: Action et menu** (AC: #4)
  - [x] Creer jsocr_correction_action
  - [x] Ajouter menu dans Apprentissage

## Dev Notes

### Technical Implementation
- Vues list, form, search pour jsocr.correction
- Action window avec list,form
- Menu sous Apprentissage, visible pour group_jsocr_manager

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- Vue liste avec decoration par type de correction
- Vue formulaire en lecture seule
- Filtres et regroupements complets
- Menu accessible sous Apprentissage

### File List

**Files created:**
- `js_invoice_ocr_ia/views/jsocr_correction_views.xml` - List, form, search views and action

**Files modified:**
- `js_invoice_ocr_ia/views/menu.xml` - Added Apprentissage submenu with Corrections entry
- `js_invoice_ocr_ia/__manifest__.py` - Added jsocr_correction_views.xml to data list

## Change Log
- **2026-02-04**: Story implemented
