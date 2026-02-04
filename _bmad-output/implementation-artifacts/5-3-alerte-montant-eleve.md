# Story 5.3: Alerte Montant Eleve

Status: done

## Story

As a **utilisateur OCR**,
I want **voir une alerte si le montant total depasse le seuil configure**,
So that **je verifie attentivement les grosses factures** (FR46).

## Acceptance Criteria

1. **AC1: Bandeau alerte**
   - **Given** une facture avec amount_total > alert_amount_threshold
   - **When** j'affiche le formulaire
   - **Then** un bandeau rouge d'alerte apparait en haut

2. **AC2: Non-bloquant**
   - **Given** une alerte montant affichee
   - **When** je clique sur Confirmer
   - **Then** la validation n'est pas bloquee

3. **AC3: Liste rouge**
   - **Given** la liste des factures OCR
   - **When** une facture depasse le seuil
   - **Then** la ligne est coloree en rouge

4. **AC4: Pas d'alerte si pas OCR**
   - **Given** une facture classique (non OCR)
   - **When** j'affiche le formulaire
   - **Then** pas de bandeau alerte JSOCR

## Tasks / Subtasks

- [x] **Task 1: Champ compute alerte** (AC: #1, #4)
  - [x] jsocr_amount_alert Boolean compute
  - [x] Compare amount_total avec config.alert_amount_threshold
  - [x] Seulement pour factures OCR

- [x] **Task 2: Bandeau dans formulaire** (AC: #1, #2)
  - [x] div alert alert-danger conditionnel
  - [x] Icone warning + message

- [x] **Task 3: Decoration liste** (AC: #3)
  - [x] decoration-danger sur liste OCR

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/account_move.py` - jsocr_amount_alert compute
- `js_invoice_ocr_ia/views/account_move_views.xml` - Alert banner + list decoration

## Change Log
- **2026-02-04**: Story implemented
