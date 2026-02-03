# Story 4.15: Notification Factures Pretes

Status: done

## Story

As a **utilisateur OCR**,
I want **etre notifie quand des factures sont pretes a valider**,
So that **je puisse agir rapidement** (FR35).

## Acceptance Criteria

1. **AC1: Notification Odoo**
   - **Given** un job passe a l'etat 'done'
   - **When** la facture brouillon est creee
   - **Then** une notification Odoo est envoyee

2. **AC2: Message notification**
   - **Given** une notification envoyee
   - **When** l'utilisateur la recoit
   - **Then** la notification indique que la facture est prete

3. **AC3: Activite sur facture**
   - **Given** une facture creee
   - **When** le job est termine
   - **Then** une activite "A faire" est creee sur la facture
   - **And** l'activite invite a valider la facture

4. **AC4: Message chatter**
   - **Given** un job termine
   - **When** la facture est creee
   - **Then** un message est poste dans le chatter du job
   - **And** le message mentionne la facture creee

## Tasks / Subtasks

- [x] **Task 1: Notification job** (AC: #1, #4)
  - [x] Methode `_send_invoice_ready_notification()`
  - [x] Message dans le chatter du job
  - [x] Type notification

- [x] **Task 2: Activite facture** (AC: #3)
  - [x] activity_schedule sur la facture
  - [x] Type: mail.mail_activity_data_todo
  - [x] Summary: "Facture OCR a valider"

- [x] **Task 3: Integration dans pipeline** (AC: #1)
  - [x] Appel apres action_mark_done
  - [x] Appel dans _process_job_async apres succes

- [x] **Task 4: Gestion erreurs** (AC: #1)
  - [x] Try/except pour eviter blocage si notification echoue
  - [x] Logger l'erreur si envoi echoue

## Dev Notes

### Notification Types
1. **Chatter message**: Notification dans le fil du job
2. **Activity**: Tache "A faire" sur la facture

### Activity Configuration
- activity_type_id: mail.mail_activity_data_todo
- summary: "Facture OCR a valider"
- note: Mentionne le fichier source
- user_id: Utilisateur courant

### Technical Requirements
- Ne pas bloquer le pipeline si notification echoue
- Logger les erreurs sans donnees sensibles
- mail.thread herite par jsocr.import.job (deja fait)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- _send_invoice_ready_notification creates chatter message
- Activity scheduled on invoice for validation
- Error handling prevents pipeline blocking
- Integrated in processing pipeline

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - _send_invoice_ready_notification

## Change Log
- **2026-02-02**: Story implemented as part of Epic 4 batch
