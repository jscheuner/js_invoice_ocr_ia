# Story 3.7: Deplacement Fichiers en Erreur

Status: done

## Story

As a **systeme**,
I want **deplacer les PDFs en erreur vers le dossier d'erreur**,
So that **les fichiers problematiques soient isoles pour analyse** (FR3).

## Acceptance Criteria

1. **AC1: Deplacement vers error_folder**
   - **Given** un job en etat 'error' ou 'failed'
   - **When** le traitement echoue definitivement
   - **Then** le PDF source est deplace vers error_folder_path

2. **AC2: Renommage avec horodatage**
   - **Given** un PDF a deplacer vers error folder
   - **When** le fichier est deplace
   - **Then** le fichier est renomme avec horodatage: YYYYMMDD_HHMMSS_original.pdf

3. **AC3: Message d'erreur stocke**
   - **Given** un job en echec
   - **When** le job est marque failed
   - **Then** le message d'erreur est stocke dans le job

4. **AC4: Email d'alerte**
   - **Given** un job echoue definitivement (failed)
   - **When** alert_email est configure
   - **Then** un email d'alerte est envoye a alert_email
   - **And** l'email contient le nom du fichier et l'erreur

5. **AC5: Logging**
   - **Given** un fichier est deplace vers error folder
   - **When** le deplacement est effectue
   - **Then** un log est cree avec le prefixe JSOCR:
   - **And** seul le nom du fichier est logge

## Tasks / Subtasks

- [x] **Task 1: Implementer methode _move_pdf_to_error** (AC: #1, #2, #5)
  - [x] Creer methode `_move_pdf_to_error()` dans jsocr.import.job
  - [x] Decoder le PDF depuis le champ binary
  - [x] Generer nom avec horodatage
  - [x] Ecrire le fichier dans error_folder_path
  - [x] Logger avec prefixe JSOCR:

- [x] **Task 2: Implementer envoi email d'alerte** (AC: #4)
  - [x] Creer methode `_send_failure_alert()`
  - [x] Envoyer email via mail.mail
  - [x] Inclure nom du fichier et message d'erreur

- [x] **Task 3: Appeler les methodes dans action_mark_failed** (AC: #1, #3, #4)
  - [x] Modifier action_mark_failed() pour appeler _move_pdf_to_error()
  - [x] Appeler _send_failure_alert()

- [x] **Task 4: Ecrire les tests** (AC: #1-#5)
  - [x] Test fichier deplace vers error folder
  - [x] Test nom avec horodatage
  - [x] Test email envoye si configure
  - [x] Test pas d'email si non configure
  - [x] Test logging

## Dev Notes

### Context from Previous Stories

**Story 3.5 patterns:**
- `_send_rejection_alert()` pour email d'alerte (dans jsocr.config)
- Format email avec nom fichier

**Modele jsocr.import.job existant:**
- Champ `error_message` pour stocker l'erreur
- Methode `action_mark_failed()` (error -> failed)

### Architecture Compliance

**Pattern Deplacement Fichier:**
```python
def _move_pdf_to_error(self):
    """Move PDF to error folder with timestamp prefix."""
    self.ensure_one()
    config = self.env['jsocr.config'].get_config()
    error_path = Path(config.error_folder_path)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest_name = f"{timestamp}_{self.pdf_filename}"
    dest_path = error_path / dest_name

    # Write PDF content to file
    pdf_content = base64.b64decode(self.pdf_file)
    dest_path.write_bytes(pdf_content)

    _logger.info("JSOCR: Job %s PDF moved to error: %s", self.id, dest_name)
```

**Pattern Email Alerte:**
```python
def _send_failure_alert(self):
    """Send email alert for failed job."""
    config = self.env['jsocr.config'].get_config()
    if not config.alert_email:
        return

    mail_values = {
        'subject': f'JSOCR: Echec traitement - {self.pdf_filename}',
        'body_html': f'''<p>Le traitement du fichier <b>{self.pdf_filename}</b> a echoue.</p>
            <p>Erreur: {self.error_message or 'Aucun detail disponible'}</p>''',
        'email_to': config.alert_email,
    }
    self.env['mail.mail'].sudo().create(mail_values).send()
```

### Technical Requirements

**Imports necessaires:**
```python
from datetime import datetime
from pathlib import Path
```

### File Structure Requirements

**Fichiers a modifier:**
1. `models/jsocr_import_job.py` - Ajouter _move_pdf_to_error(), _send_failure_alert(), modifier action_mark_failed()

### Testing Requirements

```python
def test_pdf_moved_to_error_on_failed(self):
    """Test PDF deplace vers error folder quand job failed."""
    # Creer job avec PDF, simuler erreur
    # Marquer failed
    # Verifier fichier existe dans error folder

def test_error_filename_has_timestamp(self):
    """Test nom fichier avec horodatage."""
    # Verifier format YYYYMMDD_HHMMSS_original.pdf

def test_failure_alert_email_sent(self):
    """Test email envoye si alert_email configure."""
    # Configurer alert_email
    # Marquer job failed
    # Verifier mail.mail cree

def test_no_failure_email_if_not_configured(self):
    """Test pas d'email si alert_email vide."""
    # alert_email = False
    # Marquer job failed
    # Verifier pas de mail.mail cree
```

### Git Intelligence

**Commit suggere:**
```
feat(ingestion): Move PDF to error folder on failure (Story 3.7)

- Add _move_pdf_to_error() method to jsocr.import.job
- Add _send_failure_alert() for email notifications
- Call on action_mark_failed() to archive failed PDFs
- Filename includes timestamp prefix (YYYYMMDD_HHMMSS_)
- Add tests for error file movement and alerts
```

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- **2026-02-02**: Implementation complete
  - Added `_move_pdf_to_error()` method to jsocr.import.job
  - Added `_send_failure_alert()` method for email notifications
  - Modified `action_mark_failed()` to call file movement and alert
  - Filename includes timestamp prefix (YYYYMMDD_HHMMSS_)
  - Added 4 tests for error file movement and alerts
  - All syntax checks pass

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - Added _move_pdf_to_error(), _send_failure_alert(), modified action_mark_failed()
- `js_invoice_ocr_ia/tests/test_jsocr_import_job.py` - Added 4 tests for Story 3.7
