# Story 3.4: Cron Job de Surveillance Dossier

Status: done

## Story

As a **systeme**,
I want **scanner periodiquement le dossier surveille pour detecter les nouveaux PDFs**,
So that **les factures deposees soient traitees automatiquement** (FR1).

## Acceptance Criteria

1. **AC1: Detection des PDFs dans le dossier surveille**
   - **Given** un dossier surveille configure (watch_folder_path)
   - **When** le cron s'execute
   - **Then** tous les fichiers PDF du dossier sont detectes
   - **And** les fichiers non-PDF sont ignores (traites par Story 3.5)

2. **AC2: Creation de jobs d'import**
   - **Given** un fichier PDF detecte dans le dossier
   - **When** le cron traite ce fichier
   - **Then** un jsocr.import.job est cree en etat 'pending'
   - **And** le fichier PDF est stocke dans le job (Binary)
   - **And** le nom du fichier est preserve dans pdf_filename

3. **AC3: Deplacement du fichier source**
   - **Given** un job cree avec succes
   - **When** le fichier est traite
   - **Then** le fichier est deplace du watch_folder vers un dossier temporaire/processing
   - **And** le fichier original n'est plus dans watch_folder (evite double traitement)

4. **AC4: Configuration cron 5 minutes**
   - **Given** l'addon est installe
   - **When** le cron est configure
   - **Then** il s'execute toutes les 5 minutes
   - **And** le cron est actif par defaut

5. **AC5: Performance du scan**
   - **Given** un dossier avec plusieurs fichiers
   - **When** le cron scanne le dossier
   - **Then** le scan prend moins de 10 secondes (NFR3)
   - **And** les fichiers sont traites un par un

6. **AC6: Logging sans donnees sensibles**
   - **Given** le cron s'execute
   - **When** des fichiers sont detectes
   - **Then** seuls les noms de fichiers sont logges (pas le contenu)
   - **And** le prefixe JSOCR: est utilise

## Tasks / Subtasks

- [x] **Task 1: Creer le fichier cron XML** (AC: #4)
  - [x] Creer `data/jsocr_cron.xml`
  - [x] Definir cron `ir_cron_jsocr_scan_folder` (5 minutes)
  - [x] Appeler `jsocr.config.scan_input_folder()`
  - [x] Actif par defaut

- [x] **Task 2: Implementer methode scan_input_folder** (AC: #1, #5, #6)
  - [x] Ajouter methode `scan_input_folder()` dans jsocr.config
  - [x] Lister les fichiers PDF dans watch_folder_path
  - [x] Ignorer les fichiers non-PDF (laisser pour Story 3.5)
  - [x] Logger avec prefixe JSOCR: sans contenu

- [x] **Task 3: Implementer creation de jobs** (AC: #2, #3)
  - [x] Pour chaque PDF, creer jsocr.import.job
  - [x] Lire le contenu binaire du fichier
  - [x] Stocker dans job.pdf_file (base64)
  - [x] Mettre job en etat 'pending' via action_submit()
  - [x] Supprimer fichier source apres creation (unlink)

- [x] **Task 4: Activer le cron dans le manifest** (AC: #4)
  - [x] Ajouter `data/jsocr_cron.xml` au manifest
  - [x] Verifier l'ordre de chargement

- [x] **Task 5: Ecrire les tests** (AC: #1-#6)
  - [x] Test scan dossier vide
  - [x] Test scan avec PDFs
  - [x] Test creation job correcte
  - [x] Test fichier non-PDF ignore
  - [x] Test multiples PDFs
  - [x] Test dossier inexistant

## Dev Notes

### Context from Previous Stories

**Stories 3.1-3.3 ont implemente:**
- `OCRService` avec extraction PDF natif et scanne
- Detection automatique de langue
- Champ `detected_language` sur jsocr.import.job

**Modele jsocr.config existant:**
- Champs: watch_folder_path, success_folder_path, error_folder_path, rejected_folder_path
- Methode `get_config()` pour singleton
- Validation des chemins de dossiers

### Architecture Compliance

**Pattern Cron Odoo:**
```xml
<record id="ir_cron_jsocr_scan_folder" model="ir.cron">
    <field name="name">JSOCR: Scan Input Folder</field>
    <field name="model_id" ref="model_jsocr_config"/>
    <field name="state">code</field>
    <field name="code">model.scan_input_folder()</field>
    <field name="interval_number">5</field>
    <field name="interval_type">minutes</field>
    <field name="active">True</field>
    <field name="numbercall">-1</field>
</record>
```

**Pattern Methode Scan:**
```python
@api.model
def scan_input_folder(self):
    """Scan watch folder for new PDFs and create import jobs.

    Called by ir.cron every 5 minutes.
    Creates a jsocr.import.job for each PDF found.
    """
    config = self.get_config()
    watch_path = Path(config.watch_folder_path)

    if not watch_path.exists():
        _logger.warning("JSOCR: Watch folder does not exist: %s", watch_path)
        return

    pdf_files = list(watch_path.glob('*.pdf')) + list(watch_path.glob('*.PDF'))
    _logger.info("JSOCR: Scan found %d PDF file(s)", len(pdf_files))

    for pdf_path in pdf_files:
        self._process_pdf_file(pdf_path)
```

### Conventions de nommage

- Cron ID: `ir_cron_jsocr_scan_folder`
- Methode: `scan_input_folder()` sur jsocr.config
- Logs: `JSOCR:` sans contenu fichier

### Technical Requirements

**Lecture fichier PDF:**
```python
import base64
from pathlib import Path

pdf_path = Path('/opt/jsocr/watch/invoice.pdf')
pdf_content = pdf_path.read_bytes()
pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
```

**Creation job:**
```python
job = self.env['jsocr.import.job'].create({
    'pdf_file': pdf_base64,
    'pdf_filename': pdf_path.name,
})
job.action_submit()  # draft -> pending
```

**Suppression fichier apres traitement:**
```python
pdf_path.unlink()  # Supprime le fichier
# OU
shutil.move(str(pdf_path), str(processing_path))  # Deplace
```

### File Structure Requirements

**Fichiers a creer:**
1. `data/jsocr_cron.xml` - Definition du cron job

**Fichiers a modifier:**
1. `models/jsocr_config.py` - Ajouter scan_input_folder()
2. `__manifest__.py` - Ajouter jsocr_cron.xml aux data

### Testing Requirements

```python
def test_scan_empty_folder(self):
    """Test scan avec dossier vide."""
    # Pas de fichiers = pas de jobs crees

def test_scan_with_pdfs(self):
    """Test scan avec fichiers PDF."""
    # Creer fichiers PDF de test
    # Appeler scan_input_folder()
    # Verifier jobs crees

def test_pdf_content_stored(self):
    """Test que le contenu PDF est stocke dans le job."""
    # Verifier job.pdf_file contient le bon contenu

def test_non_pdf_ignored(self):
    """Test que les fichiers non-PDF sont ignores."""
    # Creer fichier .txt
    # Appeler scan
    # Verifier aucun job cree

def test_cron_exists_and_active(self):
    """Test que le cron est configure."""
    cron = self.env.ref('js_invoice_ocr_ia.ir_cron_jsocr_scan_folder')
    self.assertTrue(cron.active)
```

### Previous Story Intelligence

**Story 3.3 patterns:**
- Tests avec `@tagged('post_install', '-at_install', 'jsocr')`
- Logs `JSOCR:` sans contenu de facture
- Integration avec jsocr.import.job

### Git Intelligence

**Commit suggere:**
```
feat(ingestion): Add folder scanning cron job (Story 3.4)

- Add ir_cron_jsocr_scan_folder (runs every 5 min)
- Add scan_input_folder() method to jsocr.config
- Create import jobs for detected PDFs
- Remove processed files from watch folder
- Add tests for folder scanning
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.4]
- [Source: _bmad-output/planning-artifacts/prd.md#FR1: surveillance dossier]
- [Source: _bmad-output/planning-artifacts/architecture.md#Cron Configuration]

### Usage in Future Stories

**Story 3.5 (Fichiers Non-PDF)** etendra ce service:
- Gerer les fichiers non-PDF detectes
- Les deplacer vers rejected_folder_path

**Story 3.6-3.7 (Deplacement fichiers)** utilisera la config:
- Deplacer vers success_folder_path ou error_folder_path

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- **2026-02-02**: Implementation complete
  - Created `data/jsocr_cron.xml` with ir_cron_jsocr_scan_folder (5 minutes interval)
  - Added `scan_input_folder()` method to jsocr.config model
  - Added `_process_pdf_file()` helper method for job creation
  - Files are deleted after job creation to prevent duplicate processing
  - Non-PDF files are ignored (left for Story 3.5)
  - Updated __manifest__.py to include cron data file
  - Added 6 tests for folder scanning functionality
  - All syntax checks pass

### File List

**Files created:**
- `js_invoice_ocr_ia/data/jsocr_cron.xml` - Cron job definition (5 min interval)

**Files modified:**
- `js_invoice_ocr_ia/models/jsocr_config.py` - Added scan_input_folder(), _process_pdf_file()
- `js_invoice_ocr_ia/__manifest__.py` - Added data/jsocr_cron.xml to data list
- `js_invoice_ocr_ia/tests/test_jsocr_config.py` - Added 6 folder scanning tests

