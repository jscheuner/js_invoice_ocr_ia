# Story 4.11: Traitement Asynchrone Queue Job

Status: done

## Story

As a **systeme**,
I want **traiter les factures en arriere-plan via queue_job**,
So that **le serveur Odoo reste reactif** (FR32).

## Acceptance Criteria

1. **AC1: Processing asynchrone**
   - **Given** un job en etat 'pending'
   - **When** le traitement est declenche
   - **Then** le traitement s'execute en arriere-plan

2. **AC2: Transition etat**
   - **Given** un job en traitement
   - **When** le processing demarre
   - **Then** l'etat passe a 'processing'
   - **And** puis a 'done' en cas de succes

3. **AC3: Isolation erreurs**
   - **Given** un job qui echoue
   - **When** l'erreur se produit
   - **Then** un echec ne bloque pas les autres jobs (NFR10)

4. **AC4: Cron de traitement**
   - **Given** des jobs en attente
   - **When** le cron s'execute
   - **Then** les jobs pending sont traites un par un

## Tasks / Subtasks

- [x] **Task 1: Implementer processing async** (AC: #1, #2)
  - [x] Methode `_process_job_async()`
  - [x] Sequence: extraction -> AI -> invoice creation
  - [x] Transitions d'etat appropriees

- [x] **Task 2: Creer le cron** (AC: #4)
  - [x] Methode `cron_process_pending_jobs()`
  - [x] Record ir.cron dans jsocr_cron.xml
  - [x] Intervalle: 1 minute

- [x] **Task 3: Isolation des erreurs** (AC: #3)
  - [x] Try/except autour de chaque job
  - [x] Continuer avec les autres jobs en cas d'erreur
  - [x] Logger les erreurs

- [x] **Task 4: Bouton traitement complet** (AC: #1)
  - [x] Methode `action_process_full()`
  - [x] Pipeline complet en un clic

## Dev Notes

### Processing Pipeline
1. Transition pending -> processing
2. Extract text (OCR)
3. Analyze with AI
4. Create draft invoice
5. Attach PDF
6. Transition processing -> done
7. Move PDF to success folder
8. Send notification

### Cron Configuration
- Name: JSOCR: Process Pending Jobs
- Interval: 1 minute
- Model: jsocr.import.job
- Method: cron_process_pending_jobs

### Technical Requirements
- NFR10: Un echec ne bloque pas les autres
- NFR1: < 2 minutes par job
- Logs sans donnees sensibles

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- _process_job_async runs full pipeline
- cron_process_pending_jobs processes up to 10 jobs
- Error isolation with try/except per job
- action_process_full for manual trigger

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - Processing methods
- `js_invoice_ocr_ia/data/jsocr_cron.xml` - ir_cron_jsocr_process_jobs

## Change Log
- **2026-02-02**: Story implemented as part of Epic 4 batch
