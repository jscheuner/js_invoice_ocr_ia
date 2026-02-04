# Story 5.6: Droits Utilisateur Standard

Status: done

## Story

As a **utilisateur OCR standard**,
I want **voir et valider uniquement mes propres factures OCR**,
So that **je ne voie que ce qui me concerne** (FR42).

## Acceptance Criteria

1. **AC1: Liste filtree**
   - **Given** je suis connecte avec jsocr.group_user uniquement
   - **When** j'accede au menu Factures OCR > Mes factures
   - **Then** je vois uniquement les factures OCR que j'ai creees

2. **AC2: Validation propres factures**
   - **Given** une facture OCR que j'ai creee
   - **When** je clique sur Confirmer
   - **Then** je peux valider la facture

3. **AC3: Jobs filtres**
   - **Given** je suis utilisateur standard
   - **When** j'accede aux jobs d'import
   - **Then** je vois uniquement mes propres jobs (ir.rule)

## Tasks / Subtasks

- [x] **Task 1: Action window filtree** (AC: #1)
  - [x] jsocr_invoice_action_mine avec domain create_uid = uid
  - [x] Menu "Mes factures" accessible a tous les utilisateurs OCR

- [x] **Task 2: Record rule sur jobs** (AC: #3)
  - [x] ir.rule sur jsocr.import.job pour group_jsocr_user
  - [x] Domain: create_uid = user.id

- [x] **Task 3: Droits validation** (AC: #2)
  - [x] Les droits Odoo natifs permettent la validation des factures

## Dev Notes

### Approach
On ne met PAS de record rules sur account.move car cela casserait
la comptabilite standard Odoo. A la place:
- Action windows avec domain filtre pour le menu OCR
- Record rules sur jsocr.import.job pour filtrer les jobs

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### File List

**Files modified:**
- `js_invoice_ocr_ia/security/jsocr_security.xml` - ir.rule for user jobs
- `js_invoice_ocr_ia/views/account_move_views.xml` - User action window
- `js_invoice_ocr_ia/views/menu.xml` - "Mes factures" menu

## Change Log
- **2026-02-04**: Story implemented
