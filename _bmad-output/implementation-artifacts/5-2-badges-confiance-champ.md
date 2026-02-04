# Story 5.2: Badges de Confiance par Champ

Status: done

## Story

As a **utilisateur OCR**,
I want **voir l'indice de confiance de chaque champ extrait**,
So that **je sache quels champs verifier en priorite** (FR22, FR45).

## Acceptance Criteria

1. **AC1: Badge confiance sur lignes**
   - **Given** une facture brouillon avec confidence_data
   - **When** j'affiche le formulaire
   - **Then** chaque ligne a un badge confiance colore

2. **AC2: Couleurs**
   - **Given** un badge de confiance
   - **When** je regarde la couleur
   - **Then** vert >= 80%, orange 50-79%, rouge < 50%

3. **AC3: Confiance globale**
   - **Given** une facture OCR
   - **When** j'ouvre l'onglet PDF
   - **Then** la confiance globale est affichee en progressbar

4. **AC4: Onglet details**
   - **Given** une facture avec confidence_data
   - **When** j'ouvre l'onglet Confiance OCR
   - **Then** je vois le detail JSON des confiances

## Tasks / Subtasks

- [x] **Task 1: Badge widget sur lignes** (AC: #1, #2)
  - [x] Colonne jsocr_account_confidence avec widget="badge"
  - [x] decoration-success/warning/danger selon seuils
  - [x] Colonne optionnelle (optional="hide")

- [x] **Task 2: Confiance globale** (AC: #3)
  - [x] Champ compute jsocr_global_confidence sur account.move
  - [x] Widget progressbar dans onglet PDF

- [x] **Task 3: Onglet confiance** (AC: #4)
  - [x] Page "Confiance OCR" avec jsocr_confidence_data

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/account_move.py` - jsocr_global_confidence compute, jsocr_confidence_badge
- `js_invoice_ocr_ia/views/account_move_views.xml` - Badge columns, confidence tab

## Change Log
- **2026-02-04**: Story implemented
