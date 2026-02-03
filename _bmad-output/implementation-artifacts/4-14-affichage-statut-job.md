# Story 4.14: Affichage Statut Job

Status: done

## Story

As a **utilisateur OCR**,
I want **voir le statut de chaque job avec indicateur visuel**,
So that **je sache rapidement ou en est le traitement** (FR34).

## Acceptance Criteria

1. **AC1: Couleurs par etat**
   - **Given** je consulte la liste des jobs
   - **When** je regarde la colonne etat
   - **Then** chaque etat a une couleur:
     - draft (gris)
     - pending (bleu)
     - processing (orange)
     - done (vert)
     - error (rouge)
     - failed (rouge fonce)

2. **AC2: Widget badge**
   - **Given** l'affichage du statut
   - **When** la colonne est rendue
   - **Then** le statut est affiche en widget badge
   - **And** la couleur correspond a l'etat

3. **AC3: Indicateur retry**
   - **Given** un job en retry
   - **When** le job a retry_count > 0
   - **Then** un badge indique le nombre de tentatives restantes
   - **And** le badge est visible dans la vue kanban

4. **AC4: Statusbar dans form**
   - **Given** la vue formulaire d'un job
   - **When** j'ouvre un job
   - **Then** un statusbar montre la progression (draft -> pending -> processing -> done)

## Tasks / Subtasks

- [x] **Task 1: Widget badge dans list** (AC: #1, #2)
  - [x] Attribut widget="badge" sur le champ state
  - [x] Decorations par etat (success, danger, warning, info, muted)

- [x] **Task 2: Indicateur retry** (AC: #3)
  - [x] Affichage retry_count dans list
  - [x] Badge retry dans kanban
  - [x] Alerte banner dans form si retry_count > 0

- [x] **Task 3: Statusbar** (AC: #4)
  - [x] Widget statusbar dans header du form
  - [x] statusbar_visible="draft,pending,processing,done"

- [x] **Task 4: Kanban styling** (AC: #1, #3)
  - [x] label_selection widget avec classes de couleur
  - [x] Badge facture creee (icon)
  - [x] Badge retry avec warning

## Dev Notes

### Badge Colors (Bootstrap)
- secondary (gris): draft
- info (bleu): pending
- warning (orange): processing
- success (vert): done
- danger (rouge): error
- dark (rouge fonce): failed

### Statusbar
Le statusbar Odoo affiche les etats visibles et highlight l'etat courant.
Les etats error/failed ne sont pas dans statusbar_visible car ce sont des fins anormales.

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- Badge widget with color decorations
- Retry indicator in list and kanban
- Alert banner in form for retry jobs
- Statusbar in form header

### File List

**Files modified:**
- `js_invoice_ocr_ia/views/jsocr_import_job_views.xml` - Status display enhancements

## Change Log
- **2026-02-02**: Story implemented as part of Epic 4 batch
