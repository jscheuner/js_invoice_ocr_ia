# Story 4.13: Vue Liste des Jobs

Status: done

## Story

As a **utilisateur OCR**,
I want **voir la liste des jobs d'importation**,
So that **je suive l'avancement des traitements** (FR33).

## Acceptance Criteria

1. **AC1: Colonnes affichees**
   - **Given** je suis connecte avec le groupe OCR
   - **When** j'accede au menu OCR IA > Jobs d'import
   - **Then** je vois une liste avec: nom fichier, date creation, etat, fournisseur detecte

2. **AC2: Filtres par etat**
   - **Given** la liste des jobs
   - **When** je veux filtrer
   - **Then** je peux filtrer par etat (draft, pending, processing, done, error, failed)

3. **AC3: Navigation vers details**
   - **Given** un job dans la liste
   - **When** je clique dessus
   - **Then** je peux voir les details du job

4. **AC4: Indicateurs visuels**
   - **Given** la liste des jobs
   - **When** je regarde la colonne etat
   - **Then** chaque etat a une couleur distinctive
   - **And** les jobs done sont en vert, error/failed en rouge

## Tasks / Subtasks

- [x] **Task 1: Creer la vue list** (AC: #1, #4)
  - [x] Record ir.ui.view jsocr_import_job_view_list
  - [x] Colonnes: name, pdf_filename, partner_id, state, detected_language, retry_count, invoice_id, create_date
  - [x] Decorations par etat

- [x] **Task 2: Creer la vue search** (AC: #2)
  - [x] Record ir.ui.view jsocr_import_job_view_search
  - [x] Filtres par etat
  - [x] Filtres avec/sans facture
  - [x] Groupes par etat, fournisseur, langue

- [x] **Task 3: Actions et menus** (AC: #3)
  - [x] Action principale jsocr_import_job_action
  - [x] Actions filtrees (pending, errors)
  - [x] Menus dans menu.xml

- [x] **Task 4: Vue kanban** (AC: #4)
  - [x] Record ir.ui.view jsocr_import_job_view_kanban
  - [x] Groupe par defaut par etat
  - [x] Affichage montant et fournisseur

## Dev Notes

### List Decorations
- success (vert): state == 'done'
- danger (rouge): state in ('error', 'failed')
- warning (orange): state == 'processing'
- info (bleu): state == 'pending'
- muted (gris): state == 'draft'

### Menu Structure
- OCR IA (root)
  - Jobs d'import
    - Tous les jobs
    - En attente
    - En erreur
  - Configuration (admin only)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- List view with all required columns
- Search view with state filters and grouping
- Kanban view grouped by state
- Multiple menu entries for quick access

### File List

**Files modified:**
- `js_invoice_ocr_ia/views/jsocr_import_job_views.xml` - List, search, kanban views
- `js_invoice_ocr_ia/views/menu.xml` - Menu structure

## Change Log
- **2026-02-02**: Story implemented as part of Epic 4 batch
