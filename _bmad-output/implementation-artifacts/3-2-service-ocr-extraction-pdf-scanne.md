# Story 3.2: Service OCR - Extraction PDF Scanne

Status: done

## Story

As a **systeme**,
I want **extraire le texte des PDFs scannes (images) via OCR**,
So that **les factures papier numerisees soient aussi traitees** (FR7).

## Acceptance Criteria

1. **AC1: Detection PDF scanne vs natif**
   - **Given** un fichier PDF
   - **When** le service OCR analyse ce fichier
   - **Then** il detecte si le PDF contient du texte selectionnable (natif) ou non (scanne)
   - **And** utilise la methode appropriee selon le type

2. **AC2: Conversion page en image**
   - **Given** un fichier PDF sans texte selectionnable (images/scan)
   - **When** le service OCR traite ce fichier
   - **Then** chaque page est convertie en image (PNG/JPEG)
   - **And** la resolution est suffisante pour l'OCR (300 DPI recommande)

3. **AC3: Extraction texte via Tesseract**
   - **Given** une image de page PDF
   - **When** Tesseract traite cette image
   - **Then** le texte est extrait avec une precision raisonnable
   - **And** les caracteres speciaux suisses (umlauts, accents) sont supportes

4. **AC4: Support multi-pages scanne**
   - **Given** un PDF scanne de plusieurs pages
   - **When** le service OCR traite ce fichier
   - **Then** le texte de toutes les pages est concatene dans l'ordre (FR8)
   - **And** chaque page est separee par un marqueur

5. **AC5: Stockage du resultat**
   - **Given** un traitement OCR reussi (natif ou scanne)
   - **When** l'extraction est terminee
   - **Then** le resultat est stocke dans jsocr.import.job.extracted_text
   - **And** le type de PDF (natif/scanne) est indique dans les logs

6. **AC6: Gestion des erreurs Tesseract**
   - **Given** Tesseract non installe ou image illisible
   - **When** le service OCR tente de traiter
   - **Then** une exception claire est levee avec un message explicatif
   - **And** le traitement ne crash pas silencieusement

## Tasks / Subtasks

- [x] **Task 1: Ajouter detection type PDF** (AC: #1)
  - [x] Modifier `_is_native_pdf()` pour retourner True/False selon presence de texte
  - [x] Ajouter methode `extract_text_from_pdf()` qui choisit la strategie
  - [x] Si texte present -> utiliser PyMuPDF (Story 3.1)
  - [x] Si pas de texte -> utiliser Tesseract OCR

- [x] **Task 2: Implementer conversion page en image** (AC: #2)
  - [x] Ajouter methode `_convert_page_to_image(page, dpi=300)`
  - [x] Utiliser PyMuPDF pour rendre la page en pixmap
  - [x] Convertir en format compatible Pillow/Tesseract

- [x] **Task 3: Implementer extraction Tesseract** (AC: #3, #6)
  - [x] Ajouter methode `_extract_text_with_tesseract(image)`
  - [x] Configurer pytesseract avec langues (fra+deu+eng)
  - [x] Gerer les erreurs Tesseract (non installe, timeout)
  - [x] Logger avec prefixe JSOCR: sans donnees sensibles

- [x] **Task 4: Implementer traitement multi-pages scanne** (AC: #4, #5)
  - [x] Boucler sur toutes les pages du PDF
  - [x] Convertir chaque page en image
  - [x] Extraire texte avec Tesseract
  - [x] Concatener avec marqueurs de page

- [x] **Task 5: Activer les dependances Python** (AC: #2, #3)
  - [x] Decommenter `pytesseract` dans `__manifest__.py`
  - [x] Decommenter `Pillow` dans `__manifest__.py`
  - [x] Verifier que les imports fonctionnent

- [x] **Task 6: Ecrire les tests** (AC: #1-#6)
  - [x] Test detection PDF natif vs scanne
  - [x] Test extraction PDF scanne simple (1 page)
  - [x] Test extraction PDF scanne multi-pages
  - [x] Test gestion erreur Tesseract non installe
  - [x] Test caracteres speciaux (umlauts, accents)

- [x] **Task 7: Mettre a jour l'export du service** (AC: #5)
  - [x] S'assurer que le service exporte les nouvelles methodes
  - [x] Documenter l'API mise a jour

### Review Follow-ups (AI)

- [x] **[AI-Review][HIGH] H1: Test integration scanned PDF → extracted_text storage** (AC: #5)
  - AC5 requiert stockage dans jsocr.import.job.extracted_text
  - Ajouter test qui cree un PDF scanne et verifie que extracted_text est bien rempli via _extract_text()
  - ✅ Tests existants dans test_jsocr_import_job.py couvrent deja l'integration _extract_text()

- [x] **[AI-Review][HIGH] H2: Test caracteres speciaux suisses avec OCR reel** (AC: #3)
  - AC3 requiert support umlauts (ü, ö, ä) et accents (é, è, ê)
  - Le test actuel verifie seulement la config langue, pas l'extraction reelle
  - ✅ Ajoute test_extract_scanned_pdf_special_characters() qui teste l'extraction OCR reelle

- [x] **[AI-Review][MEDIUM] M1: Test multi-pages scanned PDF** (AC: #4)
  - AC4 requiert concatenation ordonnee du texte multi-pages pour PDFs scannes
  - ✅ Ajoute test_extract_scanned_pdf_multipage() qui teste 3 pages avec verification de l'ordre

- [x] **[AI-Review][MEDIUM] M4: Mettre a jour File List avec tous les fichiers modifies**
  - ✅ File List mis a jour avec tous les 7 fichiers concernes

## Dev Notes

### Context from Previous Stories

**Story 3.1 a implemente:**
- `OCRService` classe dans `services/ocr_service.py`
- `extract_text_from_pdf(pdf_binary)` pour PDFs natifs
- `_is_native_pdf(pdf_binary)` pour detection (a ameliorer)
- Support multi-pages avec marqueurs `--- Page X ---`
- Gestion erreurs (PDF corrompu, protege, vide)

**Code existant a etendre:**
```python
# services/ocr_service.py - Story 3.1
class OCRService:
    def extract_text_from_pdf(self, pdf_binary):
        # Actuellement: extrait uniquement le texte natif
        # A modifier: detecter type et router vers bonne methode

    def _is_native_pdf(self, pdf_binary):
        # Existant: verifie si texte present sur premieres pages
        # A utiliser pour le routage
```

### Architecture Compliance

**Pattern Service OCR etendu:**
```python
class OCRService:
    def extract_text_from_pdf(self, pdf_binary: bytes) -> str:
        """Point d'entree principal - detecte type et extrait.

        Args:
            pdf_binary: Contenu du fichier PDF en bytes

        Returns:
            str: Texte extrait (natif ou OCR)
        """
        if self._is_native_pdf(pdf_binary):
            return self._extract_native_text(pdf_binary)
        else:
            return self._extract_scanned_text(pdf_binary)

    def _extract_native_text(self, pdf_binary: bytes) -> str:
        """Extraction PyMuPDF (Story 3.1)"""
        pass

    def _extract_scanned_text(self, pdf_binary: bytes) -> str:
        """Extraction Tesseract pour PDFs scannes"""
        pass

    def _convert_page_to_image(self, page, dpi: int = 300) -> Image:
        """Convertit une page PDF en image"""
        pass

    def _extract_text_with_tesseract(self, image: Image) -> str:
        """Extrait texte d'une image via Tesseract"""
        pass
```

**Conventions de nommage:**
- Methodes publiques: `extract_text_from_pdf()`
- Methodes privees: `_extract_native_text()`, `_extract_scanned_text()`
- Logs: `_logger.info("JSOCR: ...")` sans donnees sensibles

### Technical Requirements

**PyMuPDF - Conversion page en image:**
```python
import fitz

# Rendre une page en pixmap (image)
page = doc[page_num]
mat = fitz.Matrix(dpi/72, dpi/72)  # 300 DPI = 300/72 zoom
pixmap = page.get_pixmap(matrix=mat)

# Convertir en bytes PNG
img_bytes = pixmap.tobytes("png")

# Ou convertir en PIL Image
from PIL import Image
import io
img = Image.open(io.BytesIO(img_bytes))
```

**Tesseract - Extraction texte:**
```python
import pytesseract
from PIL import Image

# Configuration pour contexte suisse (FR/DE/EN)
config = '--psm 3 -l fra+deu+eng'

# Extraire texte
text = pytesseract.image_to_string(image, config=config)
```

**Verification Tesseract installe:**
```python
try:
    pytesseract.get_tesseract_version()
    TESSERACT_AVAILABLE = True
except pytesseract.TesseractNotFoundError:
    TESSERACT_AVAILABLE = False
```

### Library/Framework Requirements

**Dependances Python:**
- `pytesseract` - Interface Python pour Tesseract
- `Pillow` - Manipulation images

**Dependance systeme:**
- Tesseract OCR doit etre installe sur le serveur
- Packs de langue: `tesseract-ocr-fra`, `tesseract-ocr-deu`, `tesseract-ocr-eng`

**A decommenter dans __manifest__.py:**
```python
'external_dependencies': {
    'python': [
        'fitz',          # PyMuPDF (Story 3.1)
        'pytesseract',   # Interface Tesseract
        'Pillow',        # Manipulation images
    ],
},
```

### File Structure Requirements

**Fichiers a modifier:**
1. `services/ocr_service.py` - Ajouter extraction Tesseract
2. `__manifest__.py` - Activer pytesseract et Pillow
3. `tests/test_ocr_service.py` - Ajouter tests pour PDFs scannes

**Pas de nouveaux fichiers a creer** - extension du service existant.

### Testing Requirements

**Tests a ajouter (test_ocr_service.py):**

```python
def test_detect_native_pdf(self):
    """Test detection PDF avec texte selectionnable."""
    pdf_binary = create_test_pdf("Text content", num_pages=1)
    ocr = OCRService()
    self.assertTrue(ocr._is_native_pdf(pdf_binary))

def test_detect_scanned_pdf(self):
    """Test detection PDF sans texte (simule scan)."""
    # Creer PDF avec image uniquement
    pdf_binary = create_image_only_pdf()
    ocr = OCRService()
    self.assertFalse(ocr._is_native_pdf(pdf_binary))

def test_extract_scanned_pdf(self):
    """Test extraction texte d'un PDF scanne."""
    # Requires Tesseract installed
    pdf_binary = create_image_only_pdf_with_text("Facture 12345")
    ocr = OCRService()
    text = ocr.extract_text_from_pdf(pdf_binary)
    self.assertIn("Facture", text)

def test_tesseract_not_installed(self):
    """Test gestion erreur si Tesseract non installe."""
    # Mock TESSERACT_AVAILABLE = False
    pass
```

**Creer un PDF image (scan simule):**
```python
def create_image_only_pdf(text_on_image="Test"):
    """Cree un PDF contenant une image avec du texte."""
    from PIL import Image, ImageDraw, ImageFont
    import io

    # Creer image avec texte
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), text_on_image, fill='black')

    # Convertir en PDF via fitz
    doc = fitz.open()
    page = doc.new_page()

    # Inserer image dans page
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    page.insert_image(page.rect, stream=img_bytes.getvalue())

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
```

### Previous Story Intelligence

**Story 3.1 patterns:**
- Tests avec `@tagged('post_install', '-at_install', 'jsocr', 'jsocr_ocr')`
- Logs `JSOCR:` sans contenu de facture
- ValueError pour erreurs claires
- Marqueurs de page `--- Page X ---`

### Git Intelligence

**Commit suggere:**
```
feat(ocr): Add Tesseract OCR for scanned PDFs (Story 3.2)

- Extend OCRService with scanned PDF support
- Add _extract_scanned_text() with Tesseract
- Auto-detect native vs scanned PDFs
- Support fra+deu+eng languages
- Add tests for scanned PDF extraction
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.2]
- [Source: _bmad-output/planning-artifacts/architecture.md#OCRService]
- [Source: _bmad-output/planning-artifacts/prd.md#FR7: extraction PDF scannes]
- [Source: js_invoice_ocr_ia/services/ocr_service.py - code Story 3.1]

### Usage in Future Stories

**Story 3.3 (Detection Langue)** utilisera ce service:
- Analysera le texte extrait pour detecter la langue
- Pourra configurer Tesseract avec la langue detectee

**Story 3.4 (Cron Job)** utilisera ce service:
- Appellera extract_text_from_pdf() qui routera automatiquement

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- **2026-02-02**: Implementation complete
  - Extended OCRService to support scanned PDFs via Tesseract
  - Added auto-detection: _is_native_pdf() routes to correct method
  - Added _extract_native_text() for PDFs with selectable text
  - Added _extract_scanned_text() for image-based PDFs
  - Added _convert_page_to_image() with configurable DPI (default 300)
  - Added _extract_text_with_tesseract() with fra+deu+eng language support
  - Added is_tesseract_available() helper method
  - Activated external_dependencies: pytesseract, PIL
  - Added 8 new tests for scanned PDF functionality
  - Tesseract 5.5.0 verified working
  - All tests pass

- **2026-02-02**: Code Review Follow-ups addressed
  - ✅ Resolved review finding [HIGH]: H1 - Integration test coverage verified
  - ✅ Resolved review finding [HIGH]: H2 - Added test_extract_scanned_pdf_special_characters()
  - ✅ Resolved review finding [MEDIUM]: M1 - Added test_extract_scanned_pdf_multipage()
  - ✅ Resolved review finding [MEDIUM]: M4 - Updated File List with all 7 files
  - Added create_image_only_pdf() helper function for scanned PDF simulation
  - Added test_scanned_pdf_detected_correctly() for AC1 validation
  - Total tests in test_ocr_service.py: 18 tests

### File List

**Files created:**
- `js_invoice_ocr_ia/services/ocr_service.py` - OCRService with Tesseract support
- `js_invoice_ocr_ia/tests/test_ocr_service.py` - Tests for OCR service (18 tests total)

**Files modified:**
- `js_invoice_ocr_ia/__manifest__.py` - Added pytesseract and PIL dependencies
- `js_invoice_ocr_ia/services/__init__.py` - Added ocr_service import
- `js_invoice_ocr_ia/tests/__init__.py` - Added test_ocr_service import
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - Added _extract_text() method
- `js_invoice_ocr_ia/tests/test_jsocr_import_job.py` - Added OCR integration tests

## Action Items

### Deployment & System Verification

- [ ] **AI-1: Verify Tesseract installation on target server(s)**
  - Confirm Tesseract OCR 5.x is installed
  - Verify language packs are present: `tesseract-ocr-fra`, `tesseract-ocr-deu`, `tesseract-ocr-eng`
  - Test command: `tesseract --version` and `tesseract --list-langs`
  - Document installation procedure in deployment guide

- [ ] **AI-2: Configure production Tesseract settings**
  - Evaluate optimal DPI setting for production (currently 300 DPI default)
  - Consider timeout settings for large PDF processing
  - Define resource limits (memory/CPU) for Tesseract processes

### Testing & Quality

- [ ] **AI-3: End-to-end integration testing**
  - Test complete flow: upload scanned PDF → OCR extraction → field detection → validation
  - Test with real-world scanned invoices (various qualities)
  - Test with mixed PDFs (some pages native, some scanned)
  - Document test results and OCR quality baseline

- [ ] **AI-4: Performance benchmarking**
  - Measure extraction time for scanned PDFs (1-page, 5-page, 10-page)
  - Compare performance: native PDF vs scanned PDF
  - Identify performance bottlenecks if processing time > acceptable threshold
  - Document performance baseline for monitoring

- [ ] **AI-5: OCR quality validation**
  - Test with Swiss invoices containing special characters (CHF, umlauts: ä, ö, ü)
  - Test with invoices of varying image quality (150 DPI, 300 DPI, 600 DPI)
  - Measure OCR accuracy rate on sample set
  - Document known limitations (minimum quality requirements)

### Monitoring & Observability

- [ ] **AI-6: Add production monitoring metrics**
  - Track ratio of native vs scanned PDFs processed
  - Track OCR processing duration (avg, p95, p99)
  - Track OCR failures/errors
  - Add alerting for Tesseract availability issues

- [ ] **AI-7: Enhance logging for production troubleshooting**
  - Add timing logs for each OCR step (detection, conversion, extraction)
  - Log PDF type detected (native/scanned) in job metadata
  - Log Tesseract version and language config at service startup
  - Ensure no sensitive data (invoice content) in logs

### Documentation

- [ ] **AI-8: User documentation**
  - Document supported PDF types (native vs scanned)
  - Document image quality recommendations for scanning
  - Add troubleshooting guide for failed OCR extractions
  - Document expected processing times

- [ ] **AI-9: Operations documentation**
  - Create runbook for Tesseract installation and maintenance
  - Document language pack management
  - Document fallback procedures if OCR unavailable
  - Add Tesseract to system dependencies checklist

### Future Enhancements (Nice-to-Have)

- [ ] **AI-10: Optimization: Cache detection results**
  - Consider caching native/scanned detection to avoid re-detection on retry
  - Store PDF type in jsocr.import.job metadata

- [ ] **AI-11: Optimization: Parallel page processing**
  - For multi-page scanned PDFs, consider processing pages in parallel
  - Would require thread-safety assessment

- [ ] **AI-12: Enhancement: OCR confidence scoring**
  - Extract and store Tesseract confidence scores
  - Alert users when OCR confidence is low
  - Could help identify poor quality scans requiring manual review

