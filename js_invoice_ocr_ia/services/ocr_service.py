# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

"""OCR Service for extracting text from PDF files.

This service handles both native PDFs (with selectable text) and scanned PDFs:
- Native PDFs: Uses PyMuPDF (fitz) for fast text extraction
- Scanned PDFs: Uses Tesseract OCR via pytesseract

The service automatically detects the PDF type and uses the appropriate method.
"""

import io
import logging

_logger = logging.getLogger(__name__)

# Check PyMuPDF availability
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    _logger.warning("JSOCR: PyMuPDF not installed. PDF processing will not work.")

# Check Tesseract availability
try:
    import pytesseract
    from PIL import Image
    # Verify Tesseract is actually installed
    pytesseract.get_tesseract_version()
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    _logger.warning("JSOCR: pytesseract or Pillow not installed. Scanned PDF OCR disabled.")
except Exception:
    TESSERACT_AVAILABLE = False
    _logger.warning("JSOCR: Tesseract not found on system. Scanned PDF OCR disabled.")


class OCRService:
    """Service for extracting text from PDF files.

    Automatically detects PDF type and uses appropriate extraction method:
    - Native PDFs (selectable text): PyMuPDF extraction
    - Scanned PDFs (images): Tesseract OCR

    Supports multiple languages for Swiss context: French, German, English.

    Example usage:
        ocr = OCRService()
        text = ocr.extract_text_from_pdf(pdf_binary_data)
    """

    # Default OCR configuration for Swiss multilingual context
    TESSERACT_LANG = 'fra+deu+eng'
    TESSERACT_CONFIG = '--psm 3'  # Fully automatic page segmentation
    DEFAULT_DPI = 300  # Resolution for page-to-image conversion
    DEFAULT_LANGUAGE = 'fr'  # Default to French for Swiss Romandie context

    # Language detection keywords for Swiss invoice context
    # Each language has characteristic words found in invoices
    LANGUAGE_KEYWORDS = {
        'fr': [
            'facture', 'tva', 'montant', 'total', 'date', 'numero',
            'fournisseur', 'client', 'paiement', 'avoir', 'remise',
            'prix', 'quantite', 'unite', 'reference', 'livraison',
            'commande', 'conditions', 'delai', 'net', 'brut', 'ht', 'ttc',
        ],
        'de': [
            'rechnung', 'mwst', 'betrag', 'summe', 'datum', 'nummer',
            'lieferant', 'kunde', 'zahlung', 'gutschrift', 'rabatt',
            'preis', 'menge', 'einheit', 'referenz', 'lieferung',
            'bestellung', 'bedingungen', 'frist', 'netto', 'brutto',
        ],
        'en': [
            'invoice', 'vat', 'amount', 'total', 'date', 'number',
            'supplier', 'customer', 'payment', 'credit', 'discount',
            'price', 'quantity', 'unit', 'reference', 'delivery',
            'order', 'terms', 'due', 'net', 'gross', 'subtotal',
        ],
    }

    # Tesseract language code mapping (ISO 639-1 to Tesseract)
    TESSERACT_LANG_MAP = {
        'fr': 'fra',
        'de': 'deu',
        'en': 'eng',
    }

    def __init__(self):
        """Initialize OCR service and verify dependencies."""
        if not PYMUPDF_AVAILABLE:
            _logger.error("JSOCR: PyMuPDF is required but not installed")
        if not TESSERACT_AVAILABLE:
            _logger.info("JSOCR: Tesseract not available - scanned PDF OCR disabled")

    def extract_text_from_pdf(self, pdf_binary):
        """Extract text from a PDF binary (native or scanned).

        Automatically detects if the PDF contains selectable text (native)
        or is a scanned document (images), and uses the appropriate method.

        Args:
            pdf_binary (bytes): PDF file content as bytes

        Returns:
            str: Extracted text from all pages, concatenated with page markers.

        Raises:
            ValueError: If PyMuPDF is not installed
            ValueError: If pdf_binary is empty or None
            ValueError: If PDF is corrupted or invalid
            ValueError: If PDF is password protected
            ValueError: If Tesseract needed but not available
        """
        # Validate PyMuPDF availability
        if not PYMUPDF_AVAILABLE:
            raise ValueError(
                "PyMuPDF is not installed. Please install with: pip install pymupdf"
            )

        # Validate input
        if not pdf_binary:
            raise ValueError("PDF binary data is empty or None")

        _logger.info("JSOCR: Starting text extraction from PDF")

        # Detect PDF type and route to appropriate method
        if self._is_native_pdf(pdf_binary):
            _logger.info("JSOCR: Detected native PDF (selectable text)")
            return self._extract_native_text(pdf_binary)
        else:
            _logger.info("JSOCR: Detected scanned PDF (images)")
            return self._extract_scanned_text(pdf_binary)

    def _extract_native_text(self, pdf_binary):
        """Extract text from a native PDF using PyMuPDF.

        Args:
            pdf_binary (bytes): PDF file content as bytes

        Returns:
            str: Extracted text from all pages
        """
        try:
            doc = fitz.open(stream=pdf_binary, filetype="pdf")
        except Exception as e:
            _logger.error("JSOCR: Failed to open PDF: %s", type(e).__name__)
            raise ValueError(f"Invalid or corrupted PDF file: {str(e)}") from e

        try:
            if doc.is_encrypted:
                doc.close()
                _logger.warning("JSOCR: PDF is password protected")
                raise ValueError("PDF is password protected and cannot be processed")

            text_parts = []
            page_count = doc.page_count

            _logger.info("JSOCR: Processing native PDF with %d page(s)", page_count)

            for page_num in range(page_count):
                page = doc[page_num]
                page_text = page.get_text()

                text_parts.append(f"--- Page {page_num + 1} ---")
                text_parts.append(page_text.strip() if page_text else "")

            doc.close()
            full_text = "\n".join(text_parts)

            _logger.info("JSOCR: Native text extraction complete - %d page(s)", page_count)
            return full_text

        except ValueError:
            raise
        except Exception as e:
            doc.close()
            _logger.error("JSOCR: Error during native extraction: %s", type(e).__name__)
            raise ValueError(f"Error extracting text from PDF: {str(e)}") from e

    def _extract_scanned_text(self, pdf_binary):
        """Extract text from a scanned PDF using Tesseract OCR.

        Converts each page to an image and runs Tesseract OCR.

        Args:
            pdf_binary (bytes): PDF file content as bytes

        Returns:
            str: OCR-extracted text from all pages

        Raises:
            ValueError: If Tesseract is not available
        """
        if not TESSERACT_AVAILABLE:
            raise ValueError(
                "Tesseract OCR is not available. Please install Tesseract and pytesseract. "
                "On Ubuntu: apt-get install tesseract-ocr tesseract-ocr-fra tesseract-ocr-deu"
            )

        try:
            doc = fitz.open(stream=pdf_binary, filetype="pdf")
        except Exception as e:
            _logger.error("JSOCR: Failed to open PDF for OCR: %s", type(e).__name__)
            raise ValueError(f"Invalid or corrupted PDF file: {str(e)}") from e

        try:
            if doc.is_encrypted:
                doc.close()
                _logger.warning("JSOCR: PDF is password protected")
                raise ValueError("PDF is password protected and cannot be processed")

            text_parts = []
            page_count = doc.page_count

            _logger.info("JSOCR: Processing scanned PDF with %d page(s) via Tesseract", page_count)

            for page_num in range(page_count):
                page = doc[page_num]

                # Convert page to image
                image = self._convert_page_to_image(page)

                # Extract text with Tesseract
                page_text = self._extract_text_with_tesseract(image)

                text_parts.append(f"--- Page {page_num + 1} ---")
                text_parts.append(page_text.strip() if page_text else "")

                _logger.info("JSOCR: OCR completed for page %d/%d", page_num + 1, page_count)

            doc.close()
            full_text = "\n".join(text_parts)

            _logger.info("JSOCR: Scanned text extraction complete - %d page(s)", page_count)
            return full_text

        except ValueError:
            raise
        except Exception as e:
            doc.close()
            _logger.error("JSOCR: Error during OCR extraction: %s", type(e).__name__)
            raise ValueError(f"Error during OCR extraction: {str(e)}") from e

    def _convert_page_to_image(self, page, dpi=None):
        """Convert a PDF page to a PIL Image.

        Args:
            page: PyMuPDF page object
            dpi (int, optional): Resolution for rendering. Defaults to 300.

        Returns:
            PIL.Image: Rendered page as image
        """
        if dpi is None:
            dpi = self.DEFAULT_DPI

        # Calculate zoom factor (72 DPI is the base)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)

        # Render page to pixmap
        pixmap = page.get_pixmap(matrix=mat)

        # Convert to PIL Image
        img_bytes = pixmap.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))

        return image

    def _extract_text_with_tesseract(self, image):
        """Extract text from an image using Tesseract OCR.

        Args:
            image (PIL.Image): Image to process

        Returns:
            str: Extracted text

        Raises:
            ValueError: If Tesseract fails
        """
        try:
            config = f"{self.TESSERACT_CONFIG} -l {self.TESSERACT_LANG}"
            text = pytesseract.image_to_string(image, config=config)
            return text
        except Exception as e:
            _logger.error("JSOCR: Tesseract OCR failed: %s", type(e).__name__)
            raise ValueError(f"Tesseract OCR failed: {str(e)}") from e

    def _is_native_pdf(self, pdf_binary):
        """Check if PDF contains selectable text (native PDF).

        Checks the first few pages for any text content. If text is found,
        the PDF is considered native. Otherwise, it's assumed to be scanned.

        Args:
            pdf_binary (bytes): PDF file content as bytes

        Returns:
            bool: True if PDF contains selectable text, False otherwise
        """
        if not PYMUPDF_AVAILABLE:
            return False

        if not pdf_binary:
            return False

        try:
            doc = fitz.open(stream=pdf_binary, filetype="pdf")

            # Check first few pages for text
            has_text = False
            pages_to_check = min(3, doc.page_count)

            for page_num in range(pages_to_check):
                page = doc[page_num]
                text = page.get_text().strip()
                # Consider it native if we find meaningful text (> 50 chars)
                if text and len(text) > 50:
                    has_text = True
                    break

            doc.close()
            return has_text

        except Exception:
            return False

    def get_page_count(self, pdf_binary):
        """Get the number of pages in a PDF.

        Args:
            pdf_binary (bytes): PDF file content as bytes

        Returns:
            int: Number of pages in the PDF

        Raises:
            ValueError: If PDF is invalid or cannot be opened
        """
        if not PYMUPDF_AVAILABLE:
            raise ValueError("PyMuPDF is not installed")

        if not pdf_binary:
            raise ValueError("PDF binary data is empty or None")

        try:
            doc = fitz.open(stream=pdf_binary, filetype="pdf")
            count = doc.page_count
            doc.close()
            return count
        except Exception as e:
            raise ValueError(f"Cannot read PDF: {str(e)}") from e

    def is_tesseract_available(self):
        """Check if Tesseract OCR is available.

        Returns:
            bool: True if Tesseract is installed and accessible
        """
        return TESSERACT_AVAILABLE

    # -------------------------------------------------------------------------
    # LANGUAGE DETECTION (Story 3.3)
    # -------------------------------------------------------------------------

    def detect_language(self, text):
        """Detect the language of extracted text.

        Uses keyword matching to identify the most likely language among
        French, German, and English. Designed for Swiss invoice context.

        Args:
            text (str): Extracted text from PDF

        Returns:
            str: ISO 639-1 language code ('fr', 'de', or 'en')
                 Defaults to 'fr' (French) if detection is inconclusive.
        """
        if not text or not isinstance(text, str):
            _logger.info("JSOCR: Language detection - empty text, defaulting to 'fr'")
            return self.DEFAULT_LANGUAGE

        # Convert to lowercase for matching
        text_lower = text.lower()

        # Count keyword matches per language
        scores = {}
        for lang, keywords in self.LANGUAGE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[lang] = score

        # Find the language with the highest score
        max_score = max(scores.values())

        if max_score == 0:
            # No keywords matched - default to French (Swiss Romandie)
            _logger.info("JSOCR: Language detection - no keywords matched, defaulting to 'fr'")
            return self.DEFAULT_LANGUAGE

        # Get languages with max score (handle ties)
        best_langs = [lang for lang, score in scores.items() if score == max_score]

        if len(best_langs) == 1:
            detected = best_langs[0]
        else:
            # Tie - prefer French for Swiss context
            detected = 'fr' if 'fr' in best_langs else best_langs[0]
            _logger.info(
                "JSOCR: Language detection - tie between %s, selected '%s'",
                best_langs, detected
            )

        _logger.info("JSOCR: Language detected: %s (scores: fr=%d, de=%d, en=%d)",
                     detected, scores.get('fr', 0), scores.get('de', 0), scores.get('en', 0))

        return detected

    def get_tesseract_lang_config(self, detected_lang=None):
        """Get Tesseract language configuration string.

        Returns a language configuration with the detected language as primary,
        followed by other Swiss languages as fallback.

        Args:
            detected_lang (str, optional): ISO 639-1 code ('fr', 'de', 'en').
                                          Defaults to 'fr' if not provided.

        Returns:
            str: Tesseract language configuration (e.g., 'fra+deu+eng')
        """
        if detected_lang is None:
            detected_lang = self.DEFAULT_LANGUAGE

        # Map ISO code to Tesseract code
        primary = self.TESSERACT_LANG_MAP.get(detected_lang, 'fra')

        # Build config with primary language first, then others
        all_langs = ['fra', 'deu', 'eng']
        others = [lang for lang in all_langs if lang != primary]

        config = f"{primary}+{'+'.join(others)}"
        return config
