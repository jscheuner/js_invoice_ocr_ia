# Story 3.6: Deplacement Fichiers Traites avec Succes

Status: done

## Story

As a **systeme**,
I want **deplacer les PDFs traites avec succes vers le dossier de succes**,
So that **le dossier surveille reste propre** (FR2).

## Acceptance Criteria

1. **AC1: Deplacement vers success_folder**
   - **Given** un job en etat 'done' (facture creee avec succes)
   - **When** le traitement est termine
   - **Then** le PDF source est deplace vers success_folder_path

2. **AC2: Renommage avec horodatage**
   - **Given** un PDF a deplacer vers success folder
   - **When** le fichier est deplace
   - **Then** le fichier est renomme avec horodatage: YYYYMMDD_HHMMSS_original.pdf

3. **AC3: Fichier jamais supprime**
   - **Given** un job complete avec succes
   - **When** le fichier est archive
   - **Then** le fichier n'est jamais supprime (NFR12)
   - **And** le contenu PDF est preserve dans le dossier succes

4. **AC4: Logging**
   - **Given** un fichier est deplace vers success folder
   - **When** le deplacement est effectue
   - **Then** un log est cree avec le prefixe JSOCR:
   - **And** seul le nom du fichier est logge

## Tasks / Subtasks

- [x] **Task 1: Implementer methode _move_pdf_to_success** (AC: #1, #2, #3, #4)
  - [x] Creer methode `_move_pdf_to_success()` dans jsocr.import.job
  - [x] Decoder le PDF depuis le champ binary
  - [x] Generer nom avec horodatage
  - [x] Ecrire le fichier dans success_folder_path
  - [x] Logger avec prefixe JSOCR:

- [x] **Task 2: Appeler la methode dans action_mark_done** (AC: #1)
  - [x] Modifier action_mark_done() pour appeler _move_pdf_to_success()

- [x] **Task 3: Ecrire les tests** (AC: #1-#4)
  - [x] Test fichier deplace vers success folder
  - [x] Test nom avec horodatage
  - [x] Test fichier non supprime (existe dans success)
  - [x] Test logging

## Dev Notes

### Context from Previous Stories

**Story 3.4-3.5 ont implemente:**
- `scan_input_folder()` qui cree des jobs depuis les PDFs
- Le PDF est supprime de watch_folder apres creation du job
- Le PDF est stocke en base64 dans job.pdf_file

**Modele jsocr.import.job existant:**
- Champ `pdf_file` (Binary, base64)
- Champ `pdf_filename` (original filename)
- Methode `action_mark_done()` (processing -> done)

### Architecture Compliance

**Pattern Deplacement Fichier:**
```python
def _move_pdf_to_success(self):
    """Move PDF to success folder with timestamp prefix."""
    self.ensure_one()
    config = self.env['jsocr.config'].get_config()
    success_path = Path(config.success_folder_path)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest_name = f"{timestamp}_{self.pdf_filename}"
    dest_path = success_path / dest_name

    # Write PDF content to file
    pdf_content = base64.b64decode(self.pdf_file)
    dest_path.write_bytes(pdf_content)

    _logger.info("JSOCR: Job %s PDF moved to success: %s", self.id, dest_name)
```

### Technical Requirements

**Imports necessaires:**
```python
from datetime import datetime
from pathlib import Path
```

### File Structure Requirements

**Fichiers a modifier:**
1. `models/jsocr_import_job.py` - Ajouter _move_pdf_to_success(), modifier action_mark_done()

### Testing Requirements

```python
def test_pdf_moved_to_success_on_done(self):
    """Test PDF deplace vers success folder quand job done."""
    # Creer job avec PDF
    # Marquer done
    # Verifier fichier existe dans success folder

def test_success_filename_has_timestamp(self):
    """Test nom fichier avec horodatage."""
    # Verifier format YYYYMMDD_HHMMSS_original.pdf
```

### Git Intelligence

**Commit suggere:**
```
feat(ingestion): Move PDF to success folder on completion (Story 3.6)

- Add _move_pdf_to_success() method to jsocr.import.job
- Call on action_mark_done() to archive processed PDFs
- Filename includes timestamp prefix (YYYYMMDD_HHMMSS_)
- Add tests for success file movement
```

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- **2026-02-02**: Implementation complete
  - Added `_move_pdf_to_success()` method to jsocr.import.job
  - Modified `action_mark_done()` to call file movement
  - Filename includes timestamp prefix (YYYYMMDD_HHMMSS_)
  - Added 3 tests for success file movement
  - All syntax checks pass

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - Added datetime/Path imports, _move_pdf_to_success(), modified action_mark_done()
- `js_invoice_ocr_ia/tests/test_jsocr_import_job.py` - Added 3 tests for Story 3.6
