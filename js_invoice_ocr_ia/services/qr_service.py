# -*- coding: utf-8 -*-
# Part of js_invoice_ocr_ia. See LICENSE file for full copyright and licensing details.

"""Swiss QR-bill decoder service.

Decodes the Swiss QR Code (Swiss Payments Code, SPC) embedded in QR-bills.
The QR payload contains structured, 100% reliable payment data: creditor
IBAN, name and address, amount, currency, payment reference (QRR/SCOR),
and optionally Swico billing information (invoice number, date, VAT number).

Decoder backends (first available is used):
- zxing-cpp (pip install zxing-cpp) — recommended, self-contained wheels
- pyzbar (pip install pyzbar) — requires the zbar system library

If no decoder is installed, the service degrades gracefully and the
pipeline falls back to AI-only extraction.
"""

import io
import logging
import re

_logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import zxingcpp
    ZXING_AVAILABLE = True
except ImportError:
    ZXING_AVAILABLE = False

try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = PIL_AVAILABLE
except Exception:
    PYZBAR_AVAILABLE = False

# Rendering resolution for QR detection. 150 DPI is enough for the
# 46x46mm Swiss QR code and much faster than 300 DPI.
QR_RENDER_DPI = 150

# Swico billing information tags (https://www.swiss-qr-invoice.org)
SWICO_TAGS = {
    '10': 'invoice_number',
    '11': 'invoice_date',       # YYMMDD
    '20': 'customer_reference',
    '30': 'vat_number',         # IDE digits, e.g. 106017086
    '31': 'vat_date',
    '32': 'vat_details',        # e.g. "8.1" or "8.1:200;2.6:100"
    '40': 'payment_conditions',  # e.g. "2:10;0:30"
}


class SwissQRService:
    """Service to locate and parse the Swiss QR code in invoice PDFs."""

    def is_available(self):
        """Return True if a QR decoder backend and PyMuPDF are available."""
        return PYMUPDF_AVAILABLE and PIL_AVAILABLE and (ZXING_AVAILABLE or PYZBAR_AVAILABLE)

    # ------------------------------------------------------------------
    # PDF -> QR payload
    # ------------------------------------------------------------------

    def extract_qr_from_pdf(self, pdf_binary):
        """Find and parse a Swiss QR code in a PDF.

        Pages are scanned starting from the last one, since the payment
        part of a QR-bill is usually the last page.

        Args:
            pdf_binary (bytes): PDF file content

        Returns:
            dict or None: Parsed QR-bill data, or None if no Swiss QR found
        """
        if not self.is_available():
            _logger.info(
                "JSOCR: QR decoding unavailable (install zxing-cpp or pyzbar)"
            )
            return None

        if not pdf_binary:
            return None

        try:
            doc = fitz.open(stream=pdf_binary, filetype="pdf")
        except Exception as e:
            _logger.warning("JSOCR: QR scan could not open PDF: %s", type(e).__name__)
            return None

        try:
            if doc.is_encrypted:
                return None

            zoom = QR_RENDER_DPI / 72.0
            matrix = fitz.Matrix(zoom, zoom)

            for page_num in reversed(range(doc.page_count)):
                page = doc[page_num]
                pixmap = page.get_pixmap(matrix=matrix)
                image = Image.open(io.BytesIO(pixmap.tobytes("png")))

                for payload in self._decode_qr_codes(image):
                    parsed = self.parse_swiss_qr(payload)
                    if parsed:
                        _logger.info(
                            "JSOCR: Swiss QR code found on page %d", page_num + 1
                        )
                        return parsed
            return None
        finally:
            doc.close()

    def _decode_qr_codes(self, image):
        """Decode all QR codes in an image and yield their text payloads.

        Args:
            image (PIL.Image): Rendered page image

        Yields:
            str: QR code text payloads
        """
        if ZXING_AVAILABLE:
            try:
                for result in zxingcpp.read_barcodes(image):
                    if result.text:
                        yield result.text
                return
            except Exception as e:
                _logger.warning("JSOCR: zxing-cpp decode failed: %s", type(e).__name__)

        if PYZBAR_AVAILABLE:
            try:
                for result in pyzbar.decode(image):
                    if result.data:
                        yield result.data.decode('utf-8', errors='replace')
            except Exception as e:
                _logger.warning("JSOCR: pyzbar decode failed: %s", type(e).__name__)

    # ------------------------------------------------------------------
    # SPC payload parsing
    # ------------------------------------------------------------------

    def parse_swiss_qr(self, payload):
        """Parse a Swiss Payments Code (SPC) payload.

        SPC v2.0 structure (one field per line):
        0:SPC 1:version 2:coding 3:IBAN 4-10:creditor 11-17:ultimate
        creditor 18:amount 19:currency 20-26:debtor 27:ref type
        28:reference 29:unstructured message 30:EPD 31:billing info

        Args:
            payload (str): Raw QR code text

        Returns:
            dict or None: Parsed data, or None if not a Swiss QR code
        """
        if not payload:
            return None

        lines = payload.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        if not lines or lines[0].strip() != 'SPC':
            return None

        def field(index):
            return lines[index].strip() if index < len(lines) else ''

        amount = None
        if field(18):
            try:
                amount = float(field(18))
            except ValueError:
                pass

        reference_type = field(27)
        reference = field(28)

        result = {
            'version': field(1),
            'iban': field(3).replace(' ', ''),
            'creditor': {
                'name': field(5),
                'street': field(6),
                'building': field(7),
                'postal_code': field(8),
                'city': field(9),
                'country': field(10),
            },
            'amount': amount,
            'currency': field(19).upper(),
            'debtor_name': field(21),
            'reference_type': reference_type,  # QRR, SCOR or NON
            'reference': reference if reference_type in ('QRR', 'SCOR') else '',
            'unstructured_message': field(29),
            'billing_info': field(31),
        }

        result['swico'] = self.parse_swico(result['billing_info'])
        return result

    def parse_swico(self, billing_info):
        """Parse Swico billing information (//S1/...).

        Example: //S1/10/10201409/11/190512/30/106017086/32/7.7/40/0:30
        Tag 10 = invoice number, 11 = invoice date (YYMMDD),
        30 = creditor VAT number (IDE digits), 40 = payment conditions.

        Args:
            billing_info (str): Raw billing information field

        Returns:
            dict: Parsed Swico fields (empty if absent or unparseable)
        """
        if not billing_info or not billing_info.startswith('//S1/'):
            return {}

        body = billing_info[len('//S1/'):]
        # Split on tag markers "NN/" — values may contain escaped chars,
        # this pragmatic parse covers standard Swico payloads.
        parts = re.split(r'(?<!\\)/(\d{2})/', '/' + body)
        # re.split with leading '/' yields ['', tag, value, tag, value, ...]
        swico = {}
        pairs = parts[1:]
        for i in range(0, len(pairs) - 1, 2):
            tag, value = pairs[i], pairs[i + 1].rstrip('/')
            key = SWICO_TAGS.get(tag)
            if key and value:
                swico[key] = value.replace('\\/', '/')

        # Normalize the invoice date (YYMMDD -> YYYY-MM-DD)
        date_raw = swico.get('invoice_date', '')
        if re.fullmatch(r'\d{6}', date_raw):
            swico['invoice_date'] = f"20{date_raw[0:2]}-{date_raw[2:4]}-{date_raw[4:6]}"

        return swico
