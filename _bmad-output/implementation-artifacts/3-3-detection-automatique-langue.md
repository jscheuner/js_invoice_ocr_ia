# Story 3.3: Detection Automatique de Langue

Status: done

## Story

As a **systeme**,
I want **detecter automatiquement la langue du document (FR/DE/EN)**,
So that **l'OCR et l'IA utilisent la bonne langue** (FR9).

## Acceptance Criteria

1. **AC1: Detection langue par mots-cles**
   - **Given** un texte extrait d'un PDF
   - **When** le systeme analyse le texte
   - **Then** la langue est detectee parmi FR, DE, EN
   - **And** la detection utilise des mots-cles indicateurs (Facture/Rechnung/Invoice, TVA/MwSt/VAT)

2. **AC2: Stockage langue detectee**
   - **Given** une langue detectee
   - **When** l'analyse est terminee
   - **Then** la langue detectee est stockee dans le job (champ detected_language)
   - **And** la valeur est un code ISO (fr, de, en)

3. **AC3: Configuration Tesseract dynamique**
   - **Given** une langue detectee
   - **When** Tesseract traite un PDF scanne
   - **Then** Tesseract utilise le pack de langue approprie en priorite
   - **And** les autres langues restent en fallback (fra+deu+eng)

4. **AC4: Langue par defaut**
   - **Given** un texte sans indicateurs clairs de langue
   - **When** la detection echoue
   - **Then** le francais (fr) est utilise par defaut (contexte suisse romand)
   - **And** un warning est logge

5. **AC5: Logging sans donnees sensibles**
   - **Given** une detection de langue
   - **When** le resultat est logge
   - **Then** seule la langue detectee est loggee (pas le contenu du texte)
   - **And** le prefixe JSOCR: est utilise

## Tasks / Subtasks

- [x] **Task 1: Ajouter champ detected_language au modele** (AC: #2)
  - [x] Ajouter champ `detected_language` a jsocr.import.job (Selection: fr/de/en)
  - [x] Definir valeur par defaut 'fr'

- [x] **Task 2: Implementer service de detection de langue** (AC: #1, #4, #5)
  - [x] Creer methode `detect_language(text)` dans OCRService
  - [x] Definir dictionnaire de mots-cles par langue (LANGUAGE_KEYWORDS)
  - [x] Implementer algorithme de comptage/scoring
  - [x] Retourner code ISO (fr, de, en)
  - [x] Logger resultat avec prefixe JSOCR:

- [x] **Task 3: Integrer detection dans le workflow OCR** (AC: #2, #3)
  - [x] Appeler detect_language() apres extraction texte
  - [x] Stocker resultat dans job.detected_language
  - [x] Ajouter get_tesseract_lang_config() pour config dynamique

- [x] **Task 4: Ecrire les tests** (AC: #1-#5)
  - [x] Test detection texte francais (Facture, TVA, Montant)
  - [x] Test detection texte allemand (Rechnung, MwSt, Betrag)
  - [x] Test detection texte anglais (Invoice, VAT, Amount)
  - [x] Test langue par defaut si texte ambigu
  - [x] Test champ detected_language sur import.job
  - [x] Test get_tesseract_lang_config()
  - [x] Test mixed content detection
  - [x] Test empty text handling

## Dev Notes

### Context from Previous Stories

**Story 3.1 et 3.2 ont implemente:**
- `OCRService` classe dans `services/ocr_service.py`
- `extract_text_from_pdf(pdf_binary)` avec detection native/scanne
- `_extract_scanned_text()` avec Tesseract (fra+deu+eng)
- Support multi-pages avec marqueurs `--- Page X ---`

**Modele jsocr.import.job existant:**
- Champs: pdf_file, pdf_filename, state, extracted_text, ai_response, etc.
- Methode `_extract_text()` qui appelle OCRService

### Architecture Compliance

**Pattern Detection Langue:**
```python
class OCRService:
    # Mots-cles indicateurs par langue
    LANGUAGE_KEYWORDS = {
        'fr': ['facture', 'tva', 'montant', 'total', 'date', 'numero',
               'fournisseur', 'client', 'paiement', 'euros', 'chf'],
        'de': ['rechnung', 'mwst', 'betrag', 'summe', 'datum', 'nummer',
               'lieferant', 'kunde', 'zahlung', 'euro', 'chf'],
        'en': ['invoice', 'vat', 'amount', 'total', 'date', 'number',
               'supplier', 'customer', 'payment', 'usd', 'gbp'],
    }

    def detect_language(self, text: str) -> str:
        """Detecte la langue du texte extrait.

        Args:
            text: Texte extrait du PDF

        Returns:
            str: Code langue ISO (fr, de, en)
        """
        # Compter les mots-cles par langue
        # Retourner la langue avec le plus de matches
        # Default: 'fr' si egalite ou aucun match
```

**Configuration Tesseract dynamique:**
```python
def _get_tesseract_lang_config(self, detected_lang: str) -> str:
    """Retourne config Tesseract avec langue prioritaire.

    Args:
        detected_lang: Code langue detectee (fr, de, en)

    Returns:
        str: Config langue pour Tesseract (ex: 'fra+deu+eng')
    """
    lang_map = {'fr': 'fra', 'de': 'deu', 'en': 'eng'}
    primary = lang_map.get(detected_lang, 'fra')
    # Mettre la langue detectee en premier
    others = [l for l in ['fra', 'deu', 'eng'] if l != primary]
    return f"{primary}+{'+'.join(others)}"
```

### Conventions de nommage

- Champ modele: `detected_language` (snake_case)
- Valeurs: 'fr', 'de', 'en' (codes ISO 639-1)
- Logs: `_logger.info("JSOCR: Language detected: %s", lang)` sans contenu texte

### Technical Requirements

**Algorithme de detection:**
1. Convertir texte en minuscules
2. Pour chaque langue, compter les mots-cles trouves
3. Retourner la langue avec le score le plus eleve
4. Si egalite ou score = 0, retourner 'fr' (defaut suisse romand)

**Mots-cles suisses specifiques:**
- CHF (toutes langues)
- TVA 7.7% / MwSt 7.7% / VAT 7.7%
- Termes bancaires suisses

### File Structure Requirements

**Fichiers a modifier:**
1. `models/jsocr_import_job.py` - Ajouter champ detected_language
2. `services/ocr_service.py` - Ajouter detect_language()
3. `tests/test_ocr_service.py` - Ajouter tests detection langue

### Testing Requirements

```python
def test_detect_french_invoice(self):
    """Test detection langue francaise."""
    text = "Facture N: 12345\nMontant HT: 1000.00\nTVA 7.7%: 77.00"
    ocr = OCRService()
    lang = ocr.detect_language(text)
    self.assertEqual(lang, 'fr')

def test_detect_german_invoice(self):
    """Test detection langue allemande."""
    text = "Rechnung Nr: 12345\nBetrag: 1000.00\nMwSt 7.7%: 77.00"
    ocr = OCRService()
    lang = ocr.detect_language(text)
    self.assertEqual(lang, 'de')

def test_detect_english_invoice(self):
    """Test detection langue anglaise."""
    text = "Invoice No: 12345\nAmount: 1000.00\nVAT 7.7%: 77.00"
    ocr = OCRService()
    lang = ocr.detect_language(text)
    self.assertEqual(lang, 'en')

def test_detect_default_french(self):
    """Test langue par defaut si ambigu."""
    text = "12345 CHF 1000.00"  # Pas de mots-cles clairs
    ocr = OCRService()
    lang = ocr.detect_language(text)
    self.assertEqual(lang, 'fr')
```

### Previous Story Intelligence

**Story 3.2 patterns:**
- Tests avec `@tagged('post_install', '-at_install', 'jsocr', 'jsocr_ocr')`
- Logs `JSOCR:` sans contenu de facture
- ValueError pour erreurs claires

### Git Intelligence

**Commit suggere:**
```
feat(ocr): Add automatic language detection (Story 3.3)

- Add detect_language() method to OCRService
- Detect FR/DE/EN via keyword analysis
- Add detected_language field to jsocr.import.job
- Default to French for Swiss context
- Add tests for language detection
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.3]
- [Source: _bmad-output/planning-artifacts/prd.md#FR9: detection langue]
- [Source: js_invoice_ocr_ia/services/ocr_service.py]

### Usage in Future Stories

**Story 3.4 (Cron Job)** utilisera ce service:
- La langue detectee sera stockee dans le job
- Pourra etre utilisee pour l'analyse IA

**Story 4.2 (Prompt IA)** utilisera la langue detectee:
- Le prompt sera adapte selon la langue
- Meilleure precision d'extraction

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- **2026-02-02**: Implementation complete
  - Added `detected_language` field to jsocr.import.job (Selection: fr/de/en, default 'fr')
  - Added LANGUAGE_KEYWORDS dictionary with 20+ keywords per language
  - Added TESSERACT_LANG_MAP for ISO to Tesseract code mapping
  - Added `detect_language(text)` method with keyword scoring algorithm
  - Added `get_tesseract_lang_config(detected_lang)` for dynamic Tesseract config
  - Integrated language detection into `_extract_text()` workflow
  - Detection result stored in job.detected_language
  - Added 11 new tests for language detection
  - All syntax checks pass

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - Added detected_language field, updated _extract_text()
- `js_invoice_ocr_ia/services/ocr_service.py` - Added detect_language(), get_tesseract_lang_config(), LANGUAGE_KEYWORDS
- `js_invoice_ocr_ia/tests/test_ocr_service.py` - Added 11 language detection tests
- `js_invoice_ocr_ia/tests/test_jsocr_import_job.py` - Added detected_language field tests

