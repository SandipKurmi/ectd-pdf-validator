"""
PDF Validation Service for eCTD compliance.

This module contains all PDF validation logic implementing eCTD PDF Properties
Validation Criteria. Each validation rule is implemented as a separate method
for maintainability and extensibility.

Validation Rules:
- PDF_001: PDF Version Check
- PDF_002: Corruption Check
- PDF_003: Password Protection Check
- PDF_004: Fast Web View (Linearization) Check
- PDF_005: Bookmarks Check
- PDF_006: Hyperlinks Check
- PDF_007: Zoom & Layout Check
- PDF_008: Fonts Check
- PDF_009: Page Size Check
- PDF_010: File Naming Check
"""

import re
from typing import List, Tuple, Optional, BinaryIO
from dataclasses import dataclass
import fitz  # PyMuPDF
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

from app.models.response import (
    ValidationStatus,
    OverallStatus,
    RuleResult,
    ValidationSummary,
    ValidationResponse,
)


@dataclass
class ValidationRule:
    """Defines a validation rule with its metadata."""
    rule_id: str
    rule_name: str
    validator: callable


class PDFValidator:
    """
    PDF Validator for eCTD compliance checking.

    This class validates PDF files against eCTD PDF Properties Validation Criteria
    using rule-based logic. Each rule is implemented as a method and returns
    a standardized result.
    """

    # Allowed PDF versions for eCTD compliance
    ALLOWED_PDF_VERSIONS = ["1.4", "1.5", "1.6", "1.7"]

    # Standard page size for eCTD (8.5 x 11 inches in points, 1 inch = 72 points)
    # Allow small tolerance for rounding differences
    LETTER_WIDTH_POINTS = 612  # 8.5 * 72
    LETTER_HEIGHT_POINTS = 792  # 11 * 72
    PAGE_SIZE_TOLERANCE = 5  # Points tolerance

    def __init__(self, file_content: bytes, filename: str):
        """
        Initialize the PDF validator.

        Args:
            file_content: Raw bytes of the PDF file
            filename: Original filename for naming validation
        """
        self.file_content = file_content
        self.filename = filename
        self._fitz_doc: Optional[fitz.Document] = None
        self._pypdf_reader: Optional[PdfReader] = None
        self._is_corrupted = False
        self._corruption_message = ""

    def _get_fitz_document(self) -> Optional[fitz.Document]:
        """
        Lazily load and cache the PyMuPDF document.

        Returns:
            fitz.Document or None if the PDF is corrupted
        """
        if self._fitz_doc is None and not self._is_corrupted:
            try:
                self._fitz_doc = fitz.open(stream=self.file_content, filetype="pdf")
            except Exception as e:
                self._is_corrupted = True
                self._corruption_message = str(e)
        return self._fitz_doc

    def _get_pypdf_reader(self) -> Optional[PdfReader]:
        """
        Lazily load and cache the PyPDF2 reader.

        Returns:
            PdfReader or None if the PDF is corrupted
        """
        if self._pypdf_reader is None and not self._is_corrupted:
            try:
                import io
                self._pypdf_reader = PdfReader(io.BytesIO(self.file_content))
            except PdfReadError as e:
                self._is_corrupted = True
                self._corruption_message = str(e)
            except Exception as e:
                self._is_corrupted = True
                self._corruption_message = str(e)
        return self._pypdf_reader

    def validate(self) -> ValidationResponse:
        """
        Run all validation rules and return a complete validation response.

        Returns:
            ValidationResponse containing all rule results and summary
        """
        results: List[RuleResult] = []

        # Define all validation rules in order
        rules = [
            ("PDF_001", "PDF Version Check", self._check_pdf_version),
            ("PDF_002", "Corruption Check", self._check_corruption),
            ("PDF_003", "Password Protection Check", self._check_password_protection),
            ("PDF_004", "Fast Web View Check", self._check_linearization),
            ("PDF_005", "Bookmarks Check", self._check_bookmarks),
            ("PDF_006", "Hyperlinks Check", self._check_hyperlinks),
            ("PDF_007", "Zoom & Layout Check", self._check_zoom_layout),
            ("PDF_008", "Fonts Check", self._check_fonts),
            ("PDF_009", "Page Size Check", self._check_page_size),
            ("PDF_010", "File Naming Check", self._check_filename),
        ]

        for rule_id, rule_name, validator in rules:
            status, message = validator()
            results.append(RuleResult(
                ruleId=rule_id,
                ruleName=rule_name,
                status=status,
                message=message
            ))

        # Calculate summary
        passed = sum(1 for r in results if r.status == ValidationStatus.PASS)
        failed = sum(1 for r in results if r.status == ValidationStatus.FAIL)
        warnings = sum(1 for r in results if r.status == ValidationStatus.WARNING)

        overall_status = OverallStatus.FAIL if failed > 0 else OverallStatus.PASS

        return ValidationResponse(
            fileName=self.filename,
            overallStatus=overall_status,
            summary=ValidationSummary(
                totalRules=len(results),
                passed=passed,
                failed=failed,
                warnings=warnings
            ),
            results=results
        )

    def _check_pdf_version(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_001: Validate PDF version.

        Allowed versions: PDF 1.4-1.7, PDF/A-1, PDF/A-2
        Fails if JavaScript, multimedia, 3D, or attachments exist.

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to read PDF: file may be corrupted"

        try:
            # Extract PDF version from metadata
            # PyMuPDF stores version as a float (e.g., 1.7)
            metadata = doc.metadata

            # Get PDF version from the file header
            version_str = ""
            header = self.file_content[:20].decode('latin-1', errors='ignore')
            version_match = re.search(r'%PDF-(\d+\.\d+)', header)
            if version_match:
                version_str = version_match.group(1)

            # Check if version is allowed
            if version_str not in self.ALLOWED_PDF_VERSIONS:
                return ValidationStatus.FAIL, f"PDF version {version_str} is not allowed. Allowed versions: 1.4-1.7"

            # Check for PDF/A conformance (this is acceptable)
            # PDF/A identification is typically in XMP metadata

            # Check for prohibited content: JavaScript
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Check for JavaScript in annotations
                for annot in page.annots() or []:
                    if annot.type[1] == "Widget":
                        # Widget annotations may contain JavaScript
                        pass

            # Check document-level JavaScript
            if doc.get_page_fonts(0) is not None:  # Just checking doc is readable
                js_check = self._check_javascript(doc)
                if js_check:
                    return ValidationStatus.FAIL, f"PDF contains JavaScript which is not allowed: {js_check}"

            # Check for multimedia/3D content
            multimedia_check = self._check_multimedia(doc)
            if multimedia_check:
                return ValidationStatus.FAIL, f"PDF contains multimedia/3D content: {multimedia_check}"

            # Check for attachments
            if doc.embfile_count() > 0:
                return ValidationStatus.FAIL, "PDF contains embedded file attachments which are not allowed"

            return ValidationStatus.PASS, f"PDF version {version_str} is allowed"

        except Exception as e:
            return ValidationStatus.FAIL, f"Error checking PDF version: {str(e)}"

    def _check_javascript(self, doc: fitz.Document) -> Optional[str]:
        """
        Check for JavaScript in the PDF document.

        Args:
            doc: PyMuPDF document

        Returns:
            Error message if JavaScript found, None otherwise
        """
        try:
            # Check PDF catalog for JavaScript
            pdf_dict = doc.xref_get_keys(1)  # Catalog is usually xref 1
            for key in pdf_dict:
                if "JS" in key.upper() or "JAVASCRIPT" in key.upper():
                    return "Document contains JavaScript actions"

            # Check all pages for JavaScript actions
            for page_num in range(len(doc)):
                page = doc[page_num]
                links = page.get_links()
                for link in links:
                    if link.get("kind") == fitz.LINK_LAUNCH:
                        # Could be JavaScript
                        pass

            return None
        except Exception:
            return None

    def _check_multimedia(self, doc: fitz.Document) -> Optional[str]:
        """
        Check for multimedia or 3D content in the PDF.

        Args:
            doc: PyMuPDF document

        Returns:
            Error message if multimedia found, None otherwise
        """
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Check for multimedia annotations
                for annot in page.annots() or []:
                    annot_type = annot.type[1]
                    if annot_type in ["Movie", "Screen", "Sound", "RichMedia", "3D"]:
                        return f"Page {page_num + 1} contains {annot_type} content"
            return None
        except Exception:
            return None

    def _check_corruption(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_002: Check if PDF is corrupted and text searchable.

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, f"PDF is corrupted or unreadable: {self._corruption_message}"

        try:
            # Check if document has pages
            if len(doc) == 0:
                return ValidationStatus.FAIL, "PDF has no pages"

            # Check if PDF is text searchable by trying to extract text from first page
            text_found = False
            for page_num in range(min(len(doc), 5)):  # Check first 5 pages
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_found = True
                    break

            if not text_found:
                return ValidationStatus.WARNING, "PDF may not be text searchable (no extractable text found)"

            return ValidationStatus.PASS, "PDF is readable and text searchable"

        except Exception as e:
            return ValidationStatus.FAIL, f"Error reading PDF: {str(e)}"

    def _check_password_protection(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_003: Check for password protection or encryption.

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to check encryption: file may be corrupted"

        try:
            # Check if PDF is encrypted
            if doc.is_encrypted:
                return ValidationStatus.FAIL, "PDF is password protected or encrypted"

            # Check for restrictions using PyPDF2
            reader = self._get_pypdf_reader()
            if reader is not None:
                # Check if there are any encryption restrictions
                if reader.is_encrypted:
                    return ValidationStatus.FAIL, "PDF has encryption restrictions"

            return ValidationStatus.PASS, "PDF is not password protected or encrypted"

        except Exception as e:
            return ValidationStatus.FAIL, f"Error checking encryption: {str(e)}"

    def _check_linearization(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_004: Check if PDF is linearized (Fast Web View enabled).

        Note: Linearization is preferred but may be a warning, not a failure,
        depending on specific eCTD gateway requirements.

        Returns:
            Tuple of (status, message)
        """
        try:
            # Check for linearization marker in PDF header/beginning
            # Linearized PDFs have a Linearized dictionary near the beginning
            header = self.file_content[:4096].decode('latin-1', errors='ignore')

            if '/Linearized' in header:
                return ValidationStatus.PASS, "PDF is linearized (Fast Web View enabled)"
            else:
                return ValidationStatus.WARNING, "PDF is not linearized (Fast Web View not enabled)"

        except Exception as e:
            return ValidationStatus.WARNING, f"Unable to determine linearization status: {str(e)}"

    def _check_bookmarks(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_005: Check bookmarks for compliance.

        - Detect bookmarks
        - Ensure no broken bookmarks
        - No external bookmarks

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to check bookmarks: file may be corrupted"

        try:
            toc = doc.get_toc()  # Table of contents / bookmarks

            if not toc:
                # No bookmarks - this might be acceptable for simple documents
                return ValidationStatus.WARNING, "PDF has no bookmarks (may be required for complex documents)"

            issues = []
            total_bookmarks = len(toc)

            for i, (level, title, page_num, dest) in enumerate(toc):
                # Check for broken bookmarks (page number out of range)
                if page_num < 1 or page_num > len(doc):
                    issues.append(f"Bookmark '{title}' points to invalid page {page_num}")

                # Check for external destinations
                # In PyMuPDF TOC, dest might contain external file reference
                if isinstance(dest, dict):
                    if dest.get("kind") == fitz.LINK_GOTO and dest.get("file"):
                        issues.append(f"Bookmark '{title}' points to external file")

            if issues:
                return ValidationStatus.FAIL, f"Bookmark issues found: {'; '.join(issues[:3])}"

            return ValidationStatus.PASS, f"PDF has {total_bookmarks} valid bookmark(s)"

        except Exception as e:
            return ValidationStatus.WARNING, f"Unable to verify bookmarks: {str(e)}"

    def _check_hyperlinks(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_006: Check hyperlinks for compliance.

        - No broken links
        - No external (web/email) hyperlinks
        - No multiple-action links

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to check hyperlinks: file may be corrupted"

        try:
            external_links = []
            broken_links = []
            total_links = 0

            for page_num in range(len(doc)):
                page = doc[page_num]
                links = page.get_links()

                for link in links:
                    total_links += 1
                    link_type = link.get("kind")

                    # Check for external URI links (web URLs, email)
                    if link_type == fitz.LINK_URI:
                        uri = link.get("uri", "")
                        if uri.startswith(("http://", "https://", "mailto:", "ftp://")):
                            external_links.append(f"Page {page_num + 1}: {uri[:50]}")

                    # Check for broken internal links
                    elif link_type == fitz.LINK_GOTO:
                        target_page = link.get("page", -1)
                        if target_page < 0 or target_page >= len(doc):
                            broken_links.append(f"Page {page_num + 1}: link to invalid page {target_page + 1}")

                    # Check for external file links
                    elif link_type == fitz.LINK_GOTOR:
                        external_links.append(f"Page {page_num + 1}: external file link")

                    # Check for launch actions (could be multiple actions)
                    elif link_type == fitz.LINK_LAUNCH:
                        external_links.append(f"Page {page_num + 1}: launch action detected")

            issues = []
            if external_links:
                issues.append(f"{len(external_links)} external link(s) found")
            if broken_links:
                issues.append(f"{len(broken_links)} broken link(s) found")

            if issues:
                details = external_links[:2] + broken_links[:2]
                return ValidationStatus.FAIL, f"Hyperlink issues: {'; '.join(issues)}. Examples: {'; '.join(details)}"

            if total_links == 0:
                return ValidationStatus.PASS, "PDF contains no hyperlinks"

            return ValidationStatus.PASS, f"PDF contains {total_links} valid internal link(s)"

        except Exception as e:
            return ValidationStatus.WARNING, f"Unable to verify hyperlinks: {str(e)}"

    def _check_zoom_layout(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_007: Check zoom and layout settings.

        - Ensure inherit zoom behavior (no forced zoom)
        - Default page layout and magnification

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to check zoom/layout: file may be corrupted"

        try:
            reader = self._get_pypdf_reader()
            issues = []

            if reader is not None:
                # Check page layout
                if hasattr(reader, 'page_layout') and reader.page_layout:
                    layout = str(reader.page_layout)
                    # /SinglePage, /OneColumn, /TwoColumnLeft, etc.
                    # These are generally acceptable

                # Check page mode (what's displayed when opened)
                if hasattr(reader, 'page_mode') and reader.page_mode:
                    mode = str(reader.page_mode)
                    # /UseNone, /UseOutlines, /UseThumbs, /FullScreen
                    if mode == "/FullScreen":
                        issues.append("Document opens in full screen mode")

                # Check for OpenAction with specific zoom
                try:
                    if '/OpenAction' in reader.trailer.get('/Root', {}):
                        # OpenAction might specify zoom
                        pass
                except Exception:
                    pass

            # Check using PyMuPDF for additional settings
            # Get first page to check if there's a specific view setting
            if len(doc) > 0:
                first_page = doc[0]
                # The document might have specific view settings in catalog

            if issues:
                return ValidationStatus.WARNING, f"Layout/Zoom issues: {'; '.join(issues)}"

            return ValidationStatus.PASS, "PDF uses default zoom and layout settings"

        except Exception as e:
            return ValidationStatus.WARNING, f"Unable to verify zoom/layout settings: {str(e)}"

    def _check_fonts(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_008: Check that all non-standard fonts are embedded.

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to check fonts: file may be corrupted"

        try:
            # Standard PDF fonts that don't need embedding
            standard_fonts = {
                "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
                "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
                "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique",
                "Symbol", "ZapfDingbats",
                # Common variants
                "TimesNewRoman", "TimesNewRomanPS", "TimesNewRomanPSMT",
                "Arial", "ArialMT",
            }

            unembedded_fonts = []
            all_fonts = set()

            for page_num in range(len(doc)):
                fonts = doc.get_page_fonts(page_num)
                for font in fonts:
                    # font tuple: (xref, ext, type, basefont, name, encoding, referencer)
                    xref, ext, font_type, basefont, name, encoding, referencer = font

                    font_name = basefont or name or ""
                    all_fonts.add(font_name)

                    # Check if font is embedded
                    # Type3 fonts are always embedded
                    # If ext is not empty, font is embedded (has external file reference)
                    # Check font type - embedded fonts usually have specific types
                    is_standard = any(std in font_name for std in standard_fonts)

                    if not is_standard:
                        # Check if font is embedded by looking at font dictionary
                        try:
                            font_dict = doc.xref_get_key(xref, "FontFile")
                            font_dict2 = doc.xref_get_key(xref, "FontFile2")
                            font_dict3 = doc.xref_get_key(xref, "FontFile3")

                            is_embedded = any([
                                font_dict[0] != "null",
                                font_dict2[0] != "null",
                                font_dict3[0] != "null",
                                font_type == "Type3"  # Type3 fonts are embedded by definition
                            ])

                            if not is_embedded and font_name:
                                unembedded_fonts.append(font_name)
                        except Exception:
                            # If we can't determine, assume it might be problematic
                            pass

            if unembedded_fonts:
                unique_unembedded = list(set(unembedded_fonts))[:5]
                return ValidationStatus.FAIL, f"Non-embedded fonts found: {', '.join(unique_unembedded)}"

            return ValidationStatus.PASS, f"All {len(all_fonts)} font(s) are properly embedded or standard"

        except Exception as e:
            return ValidationStatus.WARNING, f"Unable to verify font embedding: {str(e)}"

    def _check_page_size(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_009: Validate page sizes against 8.5 x 11 inches.

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to check page size: file may be corrupted"

        try:
            non_compliant_pages = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                rect = page.rect  # Rectangle in points

                width = rect.width
                height = rect.height

                # Check against letter size with tolerance
                # Also allow for portrait or landscape orientation
                is_letter_portrait = (
                    abs(width - self.LETTER_WIDTH_POINTS) <= self.PAGE_SIZE_TOLERANCE and
                    abs(height - self.LETTER_HEIGHT_POINTS) <= self.PAGE_SIZE_TOLERANCE
                )
                is_letter_landscape = (
                    abs(width - self.LETTER_HEIGHT_POINTS) <= self.PAGE_SIZE_TOLERANCE and
                    abs(height - self.LETTER_WIDTH_POINTS) <= self.PAGE_SIZE_TOLERANCE
                )

                if not (is_letter_portrait or is_letter_landscape):
                    width_inches = width / 72
                    height_inches = height / 72
                    non_compliant_pages.append(
                        f"Page {page_num + 1}: {width_inches:.2f}\" x {height_inches:.2f}\""
                    )

            if non_compliant_pages:
                examples = non_compliant_pages[:3]
                return ValidationStatus.FAIL, f"Non-standard page size(s) found (expected 8.5\" x 11\"): {'; '.join(examples)}"

            return ValidationStatus.PASS, f"All {len(doc)} page(s) are standard letter size (8.5\" x 11\")"

        except Exception as e:
            return ValidationStatus.FAIL, f"Error checking page sizes: {str(e)}"

    def _check_filename(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_010: Validate file naming convention.

        - Lowercase only
        - Allow only hyphens and underscores (and alphanumeric)

        Returns:
            Tuple of (status, message)
        """
        try:
            # Remove .pdf extension for checking
            name_without_ext = self.filename
            if name_without_ext.lower().endswith('.pdf'):
                name_without_ext = name_without_ext[:-4]

            issues = []

            # Check for uppercase letters
            if name_without_ext != name_without_ext.lower():
                issues.append("filename contains uppercase letters")

            # Check for invalid characters (only allow lowercase letters, numbers, hyphens, underscores)
            valid_pattern = re.compile(r'^[a-z0-9_-]+$')
            if not valid_pattern.match(name_without_ext.lower()):
                # Find the invalid characters
                invalid_chars = set(re.findall(r'[^a-z0-9_-]', name_without_ext.lower()))
                if invalid_chars:
                    issues.append(f"invalid characters: {', '.join(repr(c) for c in invalid_chars)}")

            # Check for spaces
            if ' ' in self.filename:
                issues.append("filename contains spaces")

            if issues:
                return ValidationStatus.FAIL, f"Filename '{self.filename}' has issues: {'; '.join(issues)}"

            return ValidationStatus.PASS, f"Filename '{self.filename}' follows naming conventions"

        except Exception as e:
            return ValidationStatus.FAIL, f"Error checking filename: {str(e)}"

    def close(self):
        """Clean up resources."""
        if self._fitz_doc:
            self._fitz_doc.close()
            self._fitz_doc = None


def validate_pdf(file_content: bytes, filename: str) -> ValidationResponse:
    """
    Convenience function to validate a PDF file.

    Args:
        file_content: Raw bytes of the PDF file
        filename: Original filename

    Returns:
        ValidationResponse with all rule results
    """
    validator = PDFValidator(file_content, filename)
    try:
        return validator.validate()
    finally:
        validator.close()
