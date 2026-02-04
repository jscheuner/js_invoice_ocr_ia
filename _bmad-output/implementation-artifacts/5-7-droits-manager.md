# Story 5.7: Droits Manager

Status: done

## Story

As a **manager OCR**,
I want **voir et valider toutes les factures OCR**,
So that **je puisse superviser le travail de l'equipe** (FR43).

## Acceptance Criteria

1. **AC1: Voir toutes les factures**
   - **Given** je suis connecte avec jsocr.group_manager
   - **When** j'accede au menu Factures OCR > Toutes les factures
   - **Then** je vois toutes les factures OCR de tous les utilisateurs

2. **AC2: Validation toutes factures**
   - **Given** une facture OCR creee par un autre utilisateur
   - **When** je clique sur Confirmer
   - **Then** je peux valider la facture

3. **AC3: Tous les jobs**
   - **Given** je suis manager
   - **When** j'accede aux jobs d'import
   - **Then** je vois tous les jobs (ir.rule non restrictif)

4. **AC4: Menu specifique**
   - **Given** je suis manager
   - **When** je regarde le menu
   - **Then** je vois "Toutes les factures" (invisible pour user standard)

## Tasks / Subtasks

- [x] **Task 1: Action window sans filtre** (AC: #1)
  - [x] jsocr_invoice_action avec domain jsocr_import_job_id != False
  - [x] Pas de filtre sur create_uid

- [x] **Task 2: Record rule manager sur jobs** (AC: #3)
  - [x] ir.rule sur jsocr.import.job pour group_jsocr_manager
  - [x] Domain: [(1, '=', 1)] = voir tout

- [x] **Task 3: Menu manager** (AC: #4)
  - [x] Menu "Toutes les factures" avec groups=group_jsocr_manager
  - [x] Invisible pour utilisateurs standard

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### File List

**Files modified:**
- `js_invoice_ocr_ia/security/jsocr_security.xml` - ir.rule for manager
- `js_invoice_ocr_ia/views/account_move_views.xml` - Manager action window
- `js_invoice_ocr_ia/views/menu.xml` - "Toutes les factures" menu

## Change Log
- **2026-02-04**: Story implemented
