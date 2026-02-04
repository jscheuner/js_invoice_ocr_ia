# Story 4.19: Affichage Confiance Compte sur Lignes Facture

Status: done

## Story

As a **utilisateur OCR**,
I want **voir la confiance de prediction du compte sur chaque ligne de facture**,
So that **je sache quelles lignes verifier en priorite**.

## Acceptance Criteria

1. **AC1: Champ confiance sur ligne**
   - **Given** une facture brouillon creee par OCR avec lignes
   - **When** les lignes sont creees
   - **Then** chaque ligne a un champ jsocr_account_confidence (0-100)

2. **AC2: Source prediction**
   - **Given** une ligne avec confiance
   - **When** j'affiche le detail
   - **Then** la source est indiquee (pattern/historique/defaut)

3. **AC3: Stockage confiance**
   - **Given** une prediction effectuee
   - **When** la ligne est creee
   - **Then** la confiance et la source sont stockees

## Tasks / Subtasks

- [x] **Task 1: Ajouter champ sur account.move.line** (AC: #1)
  - [x] jsocr_account_confidence (Integer)
  - [x] jsocr_account_source (Selection: pattern/history/default)

- [x] **Task 2: Stocker confiance lors creation** (AC: #3)
  - [x] Modifier _create_invoice_lines
  - [x] Passer confidence et source aux lignes

- [x] **Task 3: Vue widget** (AC: #2)
  - [x] Widget couleur dans vue formulaire facture
  - [x] Vert >= 80, Orange 50-79, Rouge < 50

## Dev Notes

### Field Definition
```python
jsocr_account_confidence = fields.Integer(
    string='Account Confidence',
    help='Confidence score for predicted account (0-100)'
)
jsocr_account_source = fields.Selection([
    ('pattern', 'Learned Pattern'),
    ('history', 'Historical Analysis'),
    ('default', 'Default Account'),
], string='Prediction Source')
```

### Color Mapping
- >= 80%: decoration-success (green)
- 50-79%: decoration-warning (orange)
- < 50%: decoration-danger (red)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- Added confidence fields to account.move.line
- Modified _create_invoice_lines to store confidence
- Confidence passed from prediction methods

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/account_move.py` - Added confidence fields to line
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - Store confidence when creating lines

## Change Log
- **2026-02-03**: Story implemented
