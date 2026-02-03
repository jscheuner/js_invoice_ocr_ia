# Story 4.12: Gestion des Erreurs et Retry

Status: done

## Story

As a **systeme**,
I want **gerer les erreurs avec retry automatique**,
So that **les erreurs transitoires soient recuperees**.

## Acceptance Criteria

1. **AC1: Retry erreurs transitoires**
   - **Given** un job en traitement qui echoue
   - **When** l'erreur est transitoire (timeout, connexion)
   - **Then** le job est retente 3 fois avec backoff (5s, 15s, 30s)

2. **AC2: Echec apres max retries**
   - **Given** un job qui echoue 3 fois
   - **When** le max retries est atteint
   - **Then** l'etat passe a 'failed'
   - **And** le message d'erreur est stocke

3. **AC3: Erreurs permanentes**
   - **Given** une erreur permanente (parsing)
   - **When** l'erreur se produit
   - **Then** le job passe directement a 'error'
   - **And** pas de retry automatique

4. **AC4: Actions post-echec**
   - **Given** un job marque comme failed
   - **When** le statut change
   - **Then** le PDF est deplace vers error folder
   - **And** un email d'alerte est envoye

## Tasks / Subtasks

- [x] **Task 1: Implementer retry logic** (AC: #1, #2)
  - [x] Methode `_handle_processing_error(error_message, error_type)`
  - [x] Classification erreurs transitoires vs permanentes
  - [x] Incrementation retry_count
  - [x] Backoff: 5s, 15s, 30s

- [x] **Task 2: Gerer erreurs permanentes** (AC: #3)
  - [x] Liste: parse_error, validation_error
  - [x] Transition directe vers error
  - [x] Message d'erreur clair

- [x] **Task 3: Actions post-echec** (AC: #4)
  - [x] Appel _move_pdf_to_error()
  - [x] Appel _send_failure_alert()
  - [x] Gestion erreurs dans ces actions

- [x] **Task 4: Integration dans pipeline** (AC: #1-#4)
  - [x] Appel _handle_processing_error dans _process_job_async
  - [x] Gestion dans action_process_full

## Dev Notes

### Error Classification
**Transitoire (retry):**
- timeout
- connection_error
- service_unavailable

**Permanent (no retry):**
- parse_error
- validation_error

### Retry Backoff
- 1st retry: wait 5s
- 2nd retry: wait 15s
- 3rd retry: wait 30s
- After 3rd: mark as failed

### Technical Requirements
- MAX_RETRIES = 3
- RETRY_DELAYS = [5, 15, 30]
- NFR10: Un echec ne bloque pas les autres

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- _handle_processing_error implements full retry logic
- Transient vs permanent error classification
- Automatic retry scheduling
- Failed state triggers PDF move and email

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - _handle_processing_error

## Change Log
- **2026-02-02**: Story implemented as part of Epic 4 batch
