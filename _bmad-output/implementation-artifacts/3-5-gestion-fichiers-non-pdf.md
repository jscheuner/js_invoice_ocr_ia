# Story 3.5: Gestion des Fichiers Non-PDF

Status: done

## Story

As a **systeme**,
I want **rejeter les fichiers non-PDF vers un dossier dedie**,
So that **seuls les PDFs valides soient traites** (FR4).

## Acceptance Criteria

1. **AC1: Detection des fichiers non-PDF**
   - **Given** un fichier non-PDF dans le dossier surveille
   - **When** le cron scanne le dossier
   - **Then** le fichier est identifie comme non-PDF
   - **And** il n'est pas traite comme une facture

2. **AC2: Deplacement vers dossier rejected**
   - **Given** un fichier non-PDF detecte
   - **When** le systeme le traite
   - **Then** le fichier est deplace vers rejected_folder_path
   - **And** le fichier original est supprime du watch folder

3. **AC3: Gestion des doublons avec horodatage**
   - **Given** un fichier avec le meme nom existe deja dans rejected_folder
   - **When** un nouveau fichier du meme nom est rejete
   - **Then** le nom du fichier est prefixe avec horodatage (YYYYMMDD_HHMMSS_)
   - **And** les deux fichiers coexistent

4. **AC4: Email d'alerte**
   - **Given** un fichier non-PDF est rejete
   - **When** alert_email est configure
   - **Then** un email est envoye a alert_email (FR40)
   - **And** l'email contient le nom du fichier rejete

5. **AC5: Logging sans donnees sensibles**
   - **Given** un fichier est rejete
   - **When** l'evenement est logge
   - **Then** seul le nom du fichier est logge (pas le contenu)
   - **And** le prefixe JSOCR: est utilise

## Tasks / Subtasks

- [x] **Task 1: Modifier scan_input_folder pour detecter non-PDFs** (AC: #1)
  - [x] Lister tous les fichiers du dossier (pas seulement *.pdf)
  - [x] Identifier les fichiers non-PDF par extension
  - [x] Appeler une methode de rejet pour chaque non-PDF

- [x] **Task 2: Implementer methode de rejet** (AC: #2, #3, #5)
  - [x] Creer methode `_reject_non_pdf_file(file_path)`
  - [x] Deplacer vers rejected_folder_path
  - [x] Gerer les doublons avec horodatage
  - [x] Logger avec prefixe JSOCR:

- [x] **Task 3: Implementer envoi email d'alerte** (AC: #4)
  - [x] Verifier si alert_email est configure
  - [x] Envoyer email via Odoo mail template ou mail.mail
  - [x] Inclure nom du fichier dans le corps

- [x] **Task 4: Ecrire les tests** (AC: #1-#5)
  - [x] Test fichier non-PDF detecte et deplace
  - [x] Test gestion doublon avec horodatage
  - [x] Test email envoye si configure
  - [x] Test pas d'email si non configure

## Dev Notes

### Context from Previous Stories

**Story 3.4 a implemente:**
- `scan_input_folder()` qui scanne pour PDFs uniquement
- `_process_pdf_file()` pour creer des jobs
- Cron job toutes les 5 minutes

**Modele jsocr.config existant:**
- Champs: watch_folder_path, rejected_folder_path, alert_email
- Methodes: scan_input_folder(), _process_pdf_file()

### Architecture Compliance

**Extension de scan_input_folder:**
```python
@api.model
def scan_input_folder(self):
    # ... existing PDF handling ...

    # Handle non-PDF files
    all_files = list(watch_path.iterdir())
    for file_path in all_files:
        if file_path.is_file() and not file_path.suffix.lower() == '.pdf':
            self._reject_non_pdf_file(file_path)
```

**Pattern Rejet Fichier:**
```python
def _reject_non_pdf_file(self, file_path):
    """Reject a non-PDF file to rejected_folder_path.

    Args:
        file_path (Path): Path to the non-PDF file
    """
    config = self.get_config()
    rejected_path = Path(config.rejected_folder_path)

    # Generate unique filename with timestamp if duplicate
    dest_name = file_path.name
    dest_path = rejected_path / dest_name
    if dest_path.exists():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dest_name = f"{timestamp}_{file_path.name}"
        dest_path = rejected_path / dest_name

    # Move file
    shutil.move(str(file_path), str(dest_path))

    # Send alert email
    if config.alert_email:
        self._send_rejection_alert(file_path.name)

    _logger.info("JSOCR: Rejected non-PDF file: %s", file_path.name)
```

**Pattern Email Alerte:**
```python
def _send_rejection_alert(self, filename):
    """Send email alert for rejected file."""
    config = self.get_config()
    if not config.alert_email:
        return

    mail_values = {
        'subject': 'JSOCR: Fichier non-PDF rejete',
        'body_html': f'<p>Le fichier <b>{filename}</b> a ete rejete car ce n\'est pas un PDF.</p>',
        'email_to': config.alert_email,
    }
    self.env['mail.mail'].sudo().create(mail_values).send()
```

### Conventions de nommage

- Methodes: `_reject_non_pdf_file()`, `_send_rejection_alert()`
- Format horodatage: `YYYYMMDD_HHMMSS_filename.ext`
- Logs: `JSOCR:` sans contenu fichier

### Technical Requirements

**Import shutil et datetime:**
```python
import shutil
from datetime import datetime
```

**Gestion horodatage pour doublons:**
```python
from datetime import datetime

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
new_filename = f"{timestamp}_{original_filename}"
```

### File Structure Requirements

**Fichiers a modifier:**
1. `models/jsocr_config.py` - Etendre scan_input_folder, ajouter _reject_non_pdf_file

### Testing Requirements

```python
def test_non_pdf_detected_and_rejected(self):
    """Test fichier non-PDF deplace vers rejected folder."""
    # Creer fichier .txt dans watch folder
    # Appeler scan_input_folder()
    # Verifier fichier deplace vers rejected_folder

def test_duplicate_filename_with_timestamp(self):
    """Test horodatage si fichier du meme nom existe."""
    # Creer fichier dans rejected folder
    # Creer fichier du meme nom dans watch folder
    # Appeler scan
    # Verifier nouveau nom avec timestamp

def test_alert_email_sent(self):
    """Test email envoye si alert_email configure."""
    # Configurer alert_email
    # Rejeter un fichier
    # Verifier mail.mail cree

def test_no_email_if_not_configured(self):
    """Test pas d'email si alert_email vide."""
    # alert_email = False
    # Rejeter un fichier
    # Verifier pas de mail.mail cree
```

### Previous Story Intelligence

**Story 3.4 patterns:**
- `scan_input_folder()` retourne le nombre de jobs crees
- Logging JSOCR: avec nom fichier seulement
- Gestion erreurs avec try/except

### Git Intelligence

**Commit suggere:**
```
feat(ingestion): Add non-PDF file rejection (Story 3.5)

- Detect non-PDF files in watch folder
- Move rejected files to rejected_folder_path
- Add timestamp prefix for duplicate filenames
- Send email alert if configured
- Add tests for rejection handling
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.5]
- [Source: _bmad-output/planning-artifacts/prd.md#FR4: rejet non-PDF]
- [Source: _bmad-output/planning-artifacts/prd.md#FR40: email alerte]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- **2026-02-02**: Implementation complete
  - Extended `scan_input_folder()` to detect and process non-PDF files
  - Added `_reject_non_pdf_file()` method to move files to rejected_folder_path
  - Added timestamp prefix (YYYYMMDD_HHMMSS_) for duplicate filenames
  - Added `_send_rejection_alert()` method to send email via mail.mail
  - Added 5 tests for non-PDF file rejection handling
  - All syntax checks pass

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/jsocr_config.py` - Added shutil/datetime imports, _reject_non_pdf_file(), _send_rejection_alert(), extended scan_input_folder()
- `js_invoice_ocr_ia/tests/test_jsocr_config.py` - Added 5 tests for non-PDF rejection (Story 3.5)

