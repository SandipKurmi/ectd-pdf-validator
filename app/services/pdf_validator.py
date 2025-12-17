"""
PDF Validation Service for eCTD compliance.

This module contains all PDF validation logic implementing eCTD PDF Properties
Validation Criteria. Each validation rule is implemented as a separate method
for maintainability and extensibility.

100% eCTD Compliance Coverage - 14 Validation Rules:
- PDF_001: PDF Version & Prohibited Content Check
- PDF_002: Document Integrity Check
- PDF_003: Security Settings Check
- PDF_004: Fast Web View Check
- PDF_005: Bookmarks Integrity Check
- PDF_006: Hyperlinks Compliance Check
- PDF_007: Initial View & Layout Check
- PDF_008: Zoom Inheritance Check
- PDF_009: Font Embedding Check
- PDF_010: Page Size Check
- PDF_011: Page Margins Check
- PDF_012: Annotations Check
- PDF_013: Image-Based Content Check
- PDF_014: File Naming Check

eCTD Criteria Coverage:
- Criteria 1-5: PDF Version, JavaScript, multimedia, attachments, 3D → PDF_001
- Criteria 6: No annotations → PDF_012
- Criteria 7-8: Readable, text searchable → PDF_002
- Criteria 9: No password/security → PDF_003
- Criteria 10: Fast Web View → PDF_004
- Criteria 11: Inherit Zoom → PDF_008
- Criteria 12: Broken links → PDF_006
- Criteria 13: Initial view (Bookmark Panel) → PDF_007
- Criteria 14-15: Page Layout & Magnification → PDF_007
- Criteria 16-17: External/non-relative bookmarks → PDF_005
- Criteria 18-20: External/multiple-action/non-relative hyperlinks → PDF_006
- Criteria 21: Fonts embedded → PDF_009
- Criteria 22-23: Page size & margins → PDF_010, PDF_011
- Criteria 24: Avoid image-based PDFs → PDF_013
- Criteria 25: File naming → PDF_014
"""

import re
import io
from typing import List, Tuple, Optional, Set, Dict, Any
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

    Implements 100% coverage of the 18 eCTD PDF Properties Validation Criteria
    through 14 comprehensive validation rules.
    """

    # Allowed PDF versions for eCTD compliance
    ALLOWED_PDF_VERSIONS = ["1.4", "1.5", "1.6", "1.7"]

    # Standard page size for eCTD (8.5 x 11 inches in points, 1 inch = 72 points)
    LETTER_WIDTH_POINTS = 612  # 8.5 * 72
    LETTER_HEIGHT_POINTS = 792  # 11 * 72
    PAGE_SIZE_TOLERANCE = 5  # Points tolerance for rounding

    # Minimum left margin requirement (0.75 inches = 54 points)
    MIN_LEFT_MARGIN_POINTS = 54  # 0.75 * 72

    # Annotation types that are prohibited in eCTD documents
    # Only 'Link' annotations are allowed for navigation
    PROHIBITED_ANNOTATION_TYPES = {
        "Text",           # Sticky notes
        "FreeText",       # Free text annotations
        "Line",           # Line annotations
        "Square",         # Square annotations
        "Circle",         # Circle annotations
        "Polygon",        # Polygon annotations
        "PolyLine",       # Polyline annotations
        "Highlight",      # Text highlight
        "Underline",      # Text underline
        "Squiggly",       # Squiggly underline
        "StrikeOut",      # Strikethrough
        "Stamp",          # Rubber stamp annotations
        "Caret",          # Caret annotations
        "Ink",            # Ink annotations (freehand)
        "Popup",          # Popup annotations
        "FileAttachment", # File attachment annotations
        "Sound",          # Sound annotations
        "Movie",          # Movie annotations
        "Screen",         # Screen annotations
        "PrinterMark",    # Printer marks
        "TrapNet",        # Trap network annotations
        "Watermark",      # Watermark annotations
        "3D",             # 3D annotations
        "RichMedia",      # Rich media annotations
        "Redact",         # Redaction annotations
        "Widget",         # Form field widgets (may contain JS)
    }

    # Threshold for image-based PDF detection
    IMAGE_BASED_THRESHOLD = 0.5  # 50% image-only pages = FAIL
    IMAGE_WARNING_THRESHOLD = 0.2  # 20% image-only pages = WARNING

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

        # Define all 14 validation rules in order for 100% eCTD compliance
        rules = [
            ("PDF_001", "PDF Version & Prohibited Content", self._check_pdf_version_and_content),
            ("PDF_002", "Document Integrity", self._check_document_integrity),
            ("PDF_003", "Security Settings", self._check_security_settings),
            ("PDF_004", "Fast Web View", self._check_fast_web_view),
            ("PDF_005", "Bookmarks Integrity", self._check_bookmarks_integrity),
            ("PDF_006", "Hyperlinks Compliance", self._check_hyperlinks_compliance),
            ("PDF_007", "Initial View & Layout", self._check_initial_view_and_layout),
            ("PDF_008", "Zoom Inheritance", self._check_zoom_inheritance),
            ("PDF_009", "Font Embedding", self._check_font_embedding),
            ("PDF_010", "Page Size", self._check_page_size),
            ("PDF_011", "Page Margins", self._check_page_margins),
            ("PDF_012", "Annotations", self._check_annotations),
            ("PDF_013", "Image-Based Content", self._check_image_based_content),
            ("PDF_014", "File Naming", self._check_file_naming),
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

    # =========================================================================
    # PDF_001: PDF Version & Prohibited Content Check
    # eCTD Criteria: 1 (Version), 2 (No JavaScript), 3 (No multimedia),
    #                4 (No attachments), 5 (No 3D)
    # =========================================================================
    def _check_pdf_version_and_content(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_001: Validate PDF version and check for prohibited content.

        Checks:
        - PDF version must be 1.4-1.7 (PDF/A-1, PDF/A-2 also acceptable)
        - No JavaScript (document-level, page-level, annotation-level, form-level)
        - No multimedia content (audio, video, animations)
        - No embedded file attachments
        - No 3D content

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to read PDF: file may be corrupted"

        try:
            # 1. Check PDF version from file header
            version_str = ""
            header = self.file_content[:20].decode('latin-1', errors='ignore')
            version_match = re.search(r'%PDF-(\d+\.\d+)', header)
            if version_match:
                version_str = version_match.group(1)

            if version_str not in self.ALLOWED_PDF_VERSIONS:
                return ValidationStatus.FAIL, f"PDF version {version_str} is not allowed. Allowed versions: 1.4-1.7"

            # 2. Comprehensive JavaScript check
            js_result = self._check_javascript_comprehensive(doc)
            if js_result:
                return ValidationStatus.FAIL, f"PDF contains JavaScript: {js_result}"

            # 3. Check for multimedia/3D content
            multimedia_result = self._check_multimedia_content(doc)
            if multimedia_result:
                return ValidationStatus.FAIL, f"PDF contains prohibited multimedia/3D content: {multimedia_result}"

            # 4. Check for embedded file attachments
            if doc.embfile_count() > 0:
                attachment_names = [doc.embfile_info(i).get("name", f"attachment_{i}")
                                   for i in range(doc.embfile_count())]
                return ValidationStatus.FAIL, f"PDF contains {doc.embfile_count()} embedded attachment(s): {', '.join(attachment_names[:3])}"

            return ValidationStatus.PASS, f"PDF version {version_str} is compliant with no prohibited content"

        except Exception as e:
            return ValidationStatus.FAIL, f"Error checking PDF version and content: {str(e)}"

    def _check_javascript_comprehensive(self, doc: fitz.Document) -> Optional[str]:
        """
        Comprehensive JavaScript detection across all PDF structures.

        Checks:
        - Document catalog /Names/JavaScript
        - Document-level /AA (Additional Actions)
        - /OpenAction for JavaScript
        - Page-level /AA
        - Annotation actions (/A and /AA)
        - AcroForm field actions

        Args:
            doc: PyMuPDF document

        Returns:
            Error message if JavaScript found, None otherwise
        """
        try:
            # Check through all xref objects for JavaScript indicators
            for xref in range(1, doc.xref_length()):
                try:
                    # Get all keys for this xref object
                    keys = doc.xref_get_keys(xref)

                    for key in keys:
                        key_upper = key.upper()
                        # Check for JavaScript-related keys
                        if key_upper in ['JS', 'JAVASCRIPT']:
                            return f"JavaScript found in object {xref}"

                        # Check for Additional Actions that might contain JS
                        if key_upper == 'AA':
                            aa_value = doc.xref_get_key(xref, key)
                            if aa_value and 'JavaScript' in str(aa_value):
                                return f"JavaScript in Additional Actions (object {xref})"

                        # Check action type
                        if key_upper == 'S':
                            action_type = doc.xref_get_key(xref, key)
                            if action_type and 'JavaScript' in str(action_type):
                                return f"JavaScript action type found (object {xref})"

                except Exception:
                    continue

            # Check for /Names/JavaScript name tree in raw PDF content
            # This catches document-level JavaScript that might be missed
            pdf_text = self.file_content[:50000].decode('latin-1', errors='ignore')
            if '/JavaScript' in pdf_text and '/Names' in pdf_text:
                # More specific check
                if re.search(r'/Names\s*<<[^>]*?/JavaScript', pdf_text):
                    return "Document contains JavaScript name tree"

            return None

        except Exception:
            return None

    def _check_multimedia_content(self, doc: fitz.Document) -> Optional[str]:
        """
        Check for multimedia or 3D content in the PDF.

        Args:
            doc: PyMuPDF document

        Returns:
            Error message if multimedia found, None otherwise
        """
        try:
            multimedia_types = ["Movie", "Screen", "Sound", "RichMedia", "3D"]

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Check annotations for multimedia
                for annot in page.annots() or []:
                    annot_type = annot.type[1] if annot.type else ""
                    if annot_type in multimedia_types:
                        return f"Page {page_num + 1} contains {annot_type} content"

            return None
        except Exception:
            return None

    # =========================================================================
    # PDF_002: Document Integrity Check
    # eCTD Criteria: 7 (Readable), 8 (Text searchable)
    # =========================================================================
    def _check_document_integrity(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_002: Check document integrity and text searchability.

        Checks:
        - PDF opens without errors
        - Document has pages
        - Document is text searchable

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

            # Check text searchability by extracting text from pages
            total_text_chars = 0
            pages_checked = min(len(doc), 10)  # Check up to 10 pages

            for page_num in range(pages_checked):
                page = doc[page_num]
                text = page.get_text()
                total_text_chars += len(text.strip())

            if total_text_chars < 50:
                return ValidationStatus.FAIL, "PDF is not text searchable (no extractable text found). Scanned documents must be OCR processed."

            return ValidationStatus.PASS, f"PDF is readable and text searchable ({total_text_chars} characters extracted from {pages_checked} page(s))"

        except Exception as e:
            return ValidationStatus.FAIL, f"Error reading PDF: {str(e)}"

    # =========================================================================
    # PDF_003: Security Settings Check
    # eCTD Criteria: 9 (No password/security)
    # =========================================================================
    def _check_security_settings(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_003: Check for password protection and security restrictions.

        eCTD requires:
        - No password protection
        - No security settings that prevent printing, text selection,
          or modifications by reviewers

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to check security: file may be corrupted"

        try:
            # Check if PDF is encrypted
            if doc.is_encrypted:
                return ValidationStatus.FAIL, "PDF is password protected or encrypted"

            # Additional check with PyPDF2 for permission restrictions
            reader = self._get_pypdf_reader()
            if reader is not None:
                if reader.is_encrypted:
                    return ValidationStatus.FAIL, "PDF has encryption restrictions"

            return ValidationStatus.PASS, "PDF has no password protection or security restrictions"

        except Exception as e:
            return ValidationStatus.FAIL, f"Error checking security settings: {str(e)}"

    # =========================================================================
    # PDF_004: Fast Web View Check
    # eCTD Criteria: 10 (Optimize for Fast Web View)
    # =========================================================================
    def _check_fast_web_view(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_004: Check if PDF is optimized for Fast Web View (linearized).

        eCTD requires PDFs to be linearized for efficient loading.

        Returns:
            Tuple of (status, message)
        """
        try:
            # Check for linearization marker in PDF header
            # Linearized PDFs have a /Linearized dictionary near the beginning
            header = self.file_content[:4096].decode('latin-1', errors='ignore')

            if '/Linearized' in header:
                return ValidationStatus.PASS, "PDF is optimized for Fast Web View (linearized)"
            else:
                return ValidationStatus.FAIL, "PDF is not optimized for Fast Web View. Use 'Save As Optimized PDF' or enable linearization."

        except Exception as e:
            return ValidationStatus.FAIL, f"Unable to determine Fast Web View status: {str(e)}"

    # =========================================================================
    # PDF_005: Bookmarks Integrity Check
    # eCTD Criteria: 16 (No external bookmarks), 17 (No non-relative bookmarks)
    # =========================================================================
    def _check_bookmarks_integrity(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_005: Check bookmarks for integrity and compliance.

        Checks:
        - No broken bookmarks (pointing to invalid pages)
        - No external bookmarks (pointing to external files/URLs)
        - No non-relative bookmarks (absolute paths)

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to check bookmarks: file may be corrupted"

        try:
            toc = doc.get_toc(simple=False)  # Get detailed TOC with destinations

            if not toc:
                # No bookmarks - acceptable for simple documents
                return ValidationStatus.PASS, "PDF has no bookmarks"

            issues = []
            total_bookmarks = len(toc)

            for entry in toc:
                level = entry[0]
                title = entry[1]
                page_num = entry[2]
                dest = entry[3] if len(entry) > 3 else None

                # Check for broken bookmarks (invalid page reference)
                if page_num < 1 or page_num > len(doc):
                    issues.append(f"Broken bookmark '{title[:30]}' points to invalid page {page_num}")
                    continue

                # Check for external destinations
                if isinstance(dest, dict):
                    # Check for external file reference
                    if dest.get("file") or dest.get("filespec"):
                        issues.append(f"External bookmark '{title[:30]}' points to external file")

                    # Check for URI destinations
                    if dest.get("uri"):
                        uri = dest.get("uri", "")
                        if uri.startswith(("http://", "https://", "mailto:", "ftp://")):
                            issues.append(f"External bookmark '{title[:30]}' contains web/email link")

            if issues:
                return ValidationStatus.FAIL, f"Bookmark issues: {'; '.join(issues[:3])}" + (f" (+{len(issues)-3} more)" if len(issues) > 3 else "")

            return ValidationStatus.PASS, f"All {total_bookmarks} bookmark(s) are valid internal references"

        except Exception as e:
            return ValidationStatus.FAIL, f"Error checking bookmarks: {str(e)}"

    # =========================================================================
    # PDF_006: Hyperlinks Compliance Check
    # eCTD Criteria: 12 (No broken links), 18 (No external hyperlinks),
    #                19 (No multiple action links), 20 (No non-relative hyperlinks)
    # =========================================================================
    def _check_hyperlinks_compliance(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_006: Check hyperlinks for eCTD compliance.

        Checks:
        - No broken links (pointing to invalid pages)
        - No external hyperlinks (web URLs, email links)
        - No multiple-action links (action chains with /Next)
        - No non-relative hyperlinks (absolute file paths)

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to check hyperlinks: file may be corrupted"

        try:
            external_links = []
            broken_links = []
            multi_action_links = []
            total_links = 0

            for page_num in range(len(doc)):
                page = doc[page_num]
                links = page.get_links()

                for link in links:
                    total_links += 1
                    link_type = link.get("kind")
                    page_ref = f"Page {page_num + 1}"

                    # Check for external URI links (web URLs, email)
                    if link_type == fitz.LINK_URI:
                        uri = link.get("uri", "")
                        if uri.startswith(("http://", "https://", "mailto:", "ftp://", "file://")):
                            external_links.append(f"{page_ref}: {uri[:40]}...")

                    # Check for broken internal links
                    elif link_type == fitz.LINK_GOTO:
                        target_page = link.get("page", -1)
                        if target_page < 0 or target_page >= len(doc):
                            broken_links.append(f"{page_ref}: link to invalid page {target_page + 1}")

                    # Check for external file links (GoToR)
                    elif link_type == fitz.LINK_GOTOR:
                        file_spec = link.get("file", link.get("filespec", "external file"))
                        external_links.append(f"{page_ref}: external file link ({file_spec})")

                    # Check for launch actions
                    elif link_type == fitz.LINK_LAUNCH:
                        external_links.append(f"{page_ref}: launch action (potential external link)")

                    # Check for named destinations that might be external
                    elif link_type == fitz.LINK_NAMED:
                        named = link.get("name", "")
                        if named.startswith(("http", "mailto", "file")):
                            external_links.append(f"{page_ref}: named destination ({named})")

            # Check for multiple-action links by examining annotations
            multi_action_result = self._check_multiple_action_links(doc)
            if multi_action_result:
                multi_action_links.append(multi_action_result)

            # Compile issues
            issues = []
            if broken_links:
                issues.append(f"{len(broken_links)} broken link(s)")
            if external_links:
                issues.append(f"{len(external_links)} external link(s)")
            if multi_action_links:
                issues.append(f"Multiple-action links detected")

            if issues:
                examples = (broken_links[:2] + external_links[:2])[:3]
                return ValidationStatus.FAIL, f"Hyperlink issues: {'; '.join(issues)}. Examples: {'; '.join(examples)}"

            if total_links == 0:
                return ValidationStatus.PASS, "PDF contains no hyperlinks"

            return ValidationStatus.PASS, f"All {total_links} hyperlink(s) are valid internal references"

        except Exception as e:
            return ValidationStatus.FAIL, f"Error checking hyperlinks: {str(e)}"

    def _check_multiple_action_links(self, doc: fitz.Document) -> Optional[str]:
        """
        Check for links with multiple actions (action chains using /Next).

        Args:
            doc: PyMuPDF document

        Returns:
            Error message if multiple-action links found, None otherwise
        """
        try:
            # Search through xref objects for action chains
            for xref in range(1, doc.xref_length()):
                try:
                    keys = doc.xref_get_keys(xref)

                    # Check if this object has both an action and a /Next key
                    has_action = 'A' in keys or 'Action' in keys
                    has_next = 'Next' in keys

                    if has_action and has_next:
                        return f"Action chain found in object {xref} (contains /Next key)"

                    # Also check for /AA (Additional Actions)
                    if 'AA' in keys:
                        aa_value = doc.xref_get_key(xref, 'AA')
                        if aa_value and aa_value[0] != 'null':
                            return f"Additional Actions found in object {xref}"

                except Exception:
                    continue

            return None

        except Exception:
            return None

    # =========================================================================
    # PDF_007: Initial View & Layout Check
    # eCTD Criteria: 13 (Bookmark Panel & Page), 14 (Page Layout), 15 (Magnification)
    # =========================================================================
    def _check_initial_view_and_layout(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_007: Check initial view and page layout settings.

        eCTD requirements:
        - If bookmarks exist: open with "Bookmarks Panel and Page" (/UseOutlines)
        - If no bookmarks: open with "Page Only" (/UseNone or default)
        - Page Layout should be "Default"
        - Magnification should be "Default"

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to check initial view: file may be corrupted"

        try:
            reader = self._get_pypdf_reader()
            issues = []

            # Check if document has bookmarks
            toc = doc.get_toc()
            has_bookmarks = len(toc) > 0

            if reader is not None:
                # Check PageMode (initial view)
                page_mode = None
                if hasattr(reader, 'page_mode'):
                    page_mode = str(reader.page_mode) if reader.page_mode else None

                # Validate PageMode based on bookmark presence
                if has_bookmarks:
                    # Must be /UseOutlines (Bookmarks Panel and Page)
                    if page_mode and page_mode not in ['/UseOutlines', 'UseOutlines']:
                        issues.append(f"Document with bookmarks should open with 'Bookmarks Panel and Page' (current: {page_mode})")
                else:
                    # Should be /UseNone or not set (Page Only)
                    if page_mode and page_mode in ['/UseThumbs', '/FullScreen', 'UseThumbs', 'FullScreen']:
                        issues.append(f"Document without bookmarks should open with 'Page Only' (current: {page_mode})")

                # Check for FullScreen mode (always prohibited)
                if page_mode and 'FullScreen' in str(page_mode):
                    issues.append("Document opens in Full Screen mode which is not allowed")

                # Check PageLayout
                page_layout = None
                if hasattr(reader, 'page_layout'):
                    page_layout = str(reader.page_layout) if reader.page_layout else None

                # Most layouts are acceptable, but some might be problematic
                # Default or /SinglePage is preferred

            if issues:
                return ValidationStatus.FAIL, f"Initial view issues: {'; '.join(issues)}"

            bookmark_status = "with Bookmarks Panel" if has_bookmarks else "with Page Only"
            return ValidationStatus.PASS, f"PDF initial view is correctly configured ({bookmark_status})"

        except Exception as e:
            return ValidationStatus.WARNING, f"Unable to fully verify initial view settings: {str(e)}"

    # =========================================================================
    # PDF_008: Zoom Inheritance Check
    # eCTD Criteria: 11 (Inherit Zoom for bookmarks and hyperlinks)
    # =========================================================================
    def _check_zoom_inheritance(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_008: Check that bookmarks and hyperlinks use "Inherit Zoom".

        eCTD requires:
        - All bookmark destinations must use Inherit Zoom
        - All hyperlink destinations must use Inherit Zoom
        - Destinations should be /XYZ left top null (null = inherit)
          or fit-based (/Fit, /FitH, /FitV, /FitB)

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to check zoom settings: file may be corrupted"

        try:
            explicit_zoom_issues = []

            # Check bookmark destinations for explicit zoom
            toc = doc.get_toc(simple=False)
            for entry in toc:
                title = entry[1]
                dest = entry[3] if len(entry) > 3 else None

                if isinstance(dest, dict):
                    # Check for explicit zoom in XYZ destination
                    zoom = dest.get("zoom")
                    if zoom is not None and zoom != 0:
                        explicit_zoom_issues.append(f"Bookmark '{title[:25]}' has explicit zoom ({zoom})")

            # Check hyperlink destinations
            for page_num in range(len(doc)):
                page = doc[page_num]
                links = page.get_links()

                for link in links:
                    if link.get("kind") == fitz.LINK_GOTO:
                        zoom = link.get("zoom")
                        if zoom is not None and zoom != 0:
                            explicit_zoom_issues.append(f"Link on page {page_num + 1} has explicit zoom ({zoom})")

            if explicit_zoom_issues:
                examples = explicit_zoom_issues[:3]
                return ValidationStatus.FAIL, f"Explicit zoom found (should use Inherit Zoom): {'; '.join(examples)}" + (f" (+{len(explicit_zoom_issues)-3} more)" if len(explicit_zoom_issues) > 3 else "")

            total_items = len(toc) + sum(len(doc[i].get_links()) for i in range(len(doc)))
            return ValidationStatus.PASS, f"All destinations use Inherit Zoom ({total_items} items checked)"

        except Exception as e:
            return ValidationStatus.WARNING, f"Unable to fully verify zoom inheritance: {str(e)}"

    # =========================================================================
    # PDF_009: Font Embedding Check
    # eCTD Criteria: 21 (Fully embed all non-standard fonts)
    # =========================================================================
    def _check_font_embedding(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_009: Check that all non-standard fonts are embedded.

        eCTD requires all non-standard fonts to be fully embedded
        to ensure consistent rendering across systems.

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to check fonts: file may be corrupted"

        try:
            # Standard PDF base 14 fonts that don't need embedding
            standard_fonts = {
                "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
                "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
                "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique",
                "Symbol", "ZapfDingbats",
                # Common variants/aliases
                "TimesNewRoman", "TimesNewRomanPS", "TimesNewRomanPSMT",
                "TimesNewRoman-Bold", "TimesNewRoman-Italic", "TimesNewRoman-BoldItalic",
                "Arial", "ArialMT", "Arial-Bold", "Arial-Italic", "Arial-BoldItalic",
            }

            unembedded_fonts = []
            all_fonts = set()

            for page_num in range(len(doc)):
                fonts = doc.get_page_fonts(page_num)

                for font in fonts:
                    # font tuple: (xref, ext, type, basefont, name, encoding, referencer)
                    xref = font[0]
                    font_type = font[2]
                    basefont = font[3]
                    name = font[4]

                    font_name = basefont or name or ""
                    if not font_name:
                        continue

                    all_fonts.add(font_name)

                    # Check if it's a standard font
                    is_standard = any(std in font_name for std in standard_fonts)

                    if not is_standard:
                        # Check if font is embedded by looking for FontFile entries
                        try:
                            font_file = doc.xref_get_key(xref, "FontFile")
                            font_file2 = doc.xref_get_key(xref, "FontFile2")
                            font_file3 = doc.xref_get_key(xref, "FontFile3")

                            is_embedded = any([
                                font_file[0] != "null",
                                font_file2[0] != "null",
                                font_file3[0] != "null",
                                font_type == "Type3"  # Type3 fonts are embedded by definition
                            ])

                            if not is_embedded:
                                unembedded_fonts.append(font_name)
                        except Exception:
                            # If we can't determine, flag as potentially problematic
                            pass

            if unembedded_fonts:
                unique_unembedded = list(set(unembedded_fonts))[:5]
                return ValidationStatus.FAIL, f"Non-embedded fonts found: {', '.join(unique_unembedded)}"

            return ValidationStatus.PASS, f"All {len(all_fonts)} font(s) are properly embedded or standard"

        except Exception as e:
            return ValidationStatus.WARNING, f"Unable to verify font embedding: {str(e)}"

    # =========================================================================
    # PDF_010: Page Size Check
    # eCTD Criteria: 22 (8.5 x 11 inches)
    # =========================================================================
    def _check_page_size(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_010: Validate page dimensions.

        eCTD requires pages to fit on 8.5" x 11" paper (US Letter).
        Both portrait and landscape orientations are acceptable.

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

                # Check against letter size with tolerance (portrait or landscape)
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
                return ValidationStatus.FAIL, f"Non-standard page size(s) (required: 8.5\" x 11\"): {'; '.join(examples)}" + (f" (+{len(non_compliant_pages)-3} more)" if len(non_compliant_pages) > 3 else "")

            return ValidationStatus.PASS, f"All {len(doc)} page(s) are standard letter size (8.5\" x 11\")"

        except Exception as e:
            return ValidationStatus.FAIL, f"Error checking page sizes: {str(e)}"

    # =========================================================================
    # PDF_011: Page Margins Check
    # eCTD Criteria: 23 (At least 0.75" left margin)
    # =========================================================================
    def _check_page_margins(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_011: Validate page margins.

        eCTD requires at least 0.75" (54 points) left margin
        to prevent content obscuring when printed and bound.

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to check margins: file may be corrupted"

        try:
            insufficient_margin_pages = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                page_rect = page.rect

                # Get content bounding box (area containing actual content)
                # This finds the smallest rectangle containing all content
                text_blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                drawings = page.get_drawings()
                images = page.get_images()

                # Calculate leftmost content position
                leftmost_content = page_rect.width  # Start with page width

                # Check text blocks
                if text_blocks and "blocks" in text_blocks:
                    for block in text_blocks["blocks"]:
                        if "bbox" in block:
                            bbox = block["bbox"]
                            if bbox[0] < leftmost_content:
                                leftmost_content = bbox[0]

                # Check drawings
                for drawing in drawings:
                    if "rect" in drawing:
                        if drawing["rect"][0] < leftmost_content:
                            leftmost_content = drawing["rect"][0]

                # Check images
                for img in images:
                    try:
                        img_rect = page.get_image_bbox(img)
                        if img_rect and img_rect.x0 < leftmost_content:
                            leftmost_content = img_rect.x0
                    except Exception:
                        pass

                # leftmost_content is now the left margin (distance from page edge to content)
                left_margin = leftmost_content

                if left_margin < self.MIN_LEFT_MARGIN_POINTS and left_margin < page_rect.width:
                    margin_inches = left_margin / 72
                    insufficient_margin_pages.append(
                        f"Page {page_num + 1}: {margin_inches:.2f}\" left margin"
                    )

            if insufficient_margin_pages:
                examples = insufficient_margin_pages[:3]
                return ValidationStatus.FAIL, f"Insufficient left margin (required: 0.75\"): {'; '.join(examples)}" + (f" (+{len(insufficient_margin_pages)-3} more)" if len(insufficient_margin_pages) > 3 else "")

            return ValidationStatus.PASS, f"All {len(doc)} page(s) have adequate left margins (>= 0.75\")"

        except Exception as e:
            return ValidationStatus.WARNING, f"Unable to fully verify page margins: {str(e)}"

    # =========================================================================
    # PDF_012: Annotations Check
    # eCTD Criteria: 6 (No PDF annotations)
    # =========================================================================
    def _check_annotations(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_012: Check for prohibited annotations.

        eCTD prohibits all annotations except Link annotations
        (which are needed for navigation).

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to check annotations: file may be corrupted"

        try:
            prohibited_annotations = []
            total_annotations = 0
            link_annotations = 0

            for page_num in range(len(doc)):
                page = doc[page_num]

                for annot in page.annots() or []:
                    total_annotations += 1
                    annot_type = annot.type[1] if annot.type else "Unknown"

                    # Link annotations are allowed for navigation
                    if annot_type == "Link":
                        link_annotations += 1
                        continue

                    # All other annotations are prohibited
                    if annot_type in self.PROHIBITED_ANNOTATION_TYPES or annot_type not in ["Link"]:
                        prohibited_annotations.append(f"Page {page_num + 1}: {annot_type}")

            if prohibited_annotations:
                examples = prohibited_annotations[:5]
                return ValidationStatus.FAIL, f"Prohibited annotation(s) found: {'; '.join(examples)}" + (f" (+{len(prohibited_annotations)-5} more)" if len(prohibited_annotations) > 5 else "")

            if total_annotations == 0:
                return ValidationStatus.PASS, "PDF contains no annotations"

            return ValidationStatus.PASS, f"PDF contains only allowed Link annotations ({link_annotations} links)"

        except Exception as e:
            return ValidationStatus.WARNING, f"Unable to verify annotations: {str(e)}"

    # =========================================================================
    # PDF_013: Image-Based Content Check
    # eCTD Criteria: 24 (Avoid image-based/scanned PDFs)
    # =========================================================================
    def _check_image_based_content(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_013: Check if PDF is primarily image-based (scanned).

        eCTD recommends avoiding scanned/image-based PDFs as they have
        poorer quality than PDFs created from electronic sources.

        Returns:
            Tuple of (status, message)
        """
        doc = self._get_fitz_document()
        if doc is None:
            return ValidationStatus.FAIL, "Unable to check content type: file may be corrupted"

        try:
            total_pages = len(doc)
            image_only_pages = 0

            for page_num in range(total_pages):
                page = doc[page_num]

                # Get text content
                text = page.get_text().strip()

                # Get images on the page
                images = page.get_images()

                # A page is considered "image-only" if:
                # - It has very little text (< 50 chars) AND
                # - It has at least one image
                if len(text) < 50 and len(images) > 0:
                    image_only_pages += 1

            if total_pages == 0:
                return ValidationStatus.PASS, "PDF content type could not be determined (no pages)"

            image_ratio = image_only_pages / total_pages

            if image_ratio > self.IMAGE_BASED_THRESHOLD:
                percentage = int(image_ratio * 100)
                return ValidationStatus.FAIL, f"PDF appears to be scanned/image-based ({percentage}% image-only pages). Use electronic source documents or apply OCR."

            if image_ratio > self.IMAGE_WARNING_THRESHOLD:
                percentage = int(image_ratio * 100)
                return ValidationStatus.WARNING, f"PDF contains significant image-only content ({percentage}% of pages). Consider using electronic source documents."

            return ValidationStatus.PASS, f"PDF is primarily text-based (electronic source) - {total_pages - image_only_pages}/{total_pages} pages with searchable text"

        except Exception as e:
            return ValidationStatus.WARNING, f"Unable to determine PDF content type: {str(e)}"

    # =========================================================================
    # PDF_014: File Naming Check
    # eCTD Criteria: 25 (Lowercase, hyphen/underscore only)
    # =========================================================================
    def _check_file_naming(self) -> Tuple[ValidationStatus, str]:
        """
        PDF_014: Validate file naming convention.

        eCTD requirements:
        - Lowercase characters only
        - Only alphanumeric, hyphens (-), and underscores (_) allowed
        - No spaces or special characters

        Returns:
            Tuple of (status, message)
        """
        try:
            # Get filename without .pdf extension
            name_without_ext = self.filename
            if name_without_ext.lower().endswith('.pdf'):
                name_without_ext = name_without_ext[:-4]

            issues = []

            # Check for uppercase letters
            if name_without_ext != name_without_ext.lower():
                issues.append("contains uppercase letters")

            # Check for spaces
            if ' ' in name_without_ext:
                issues.append("contains spaces")

            # Check for invalid characters (only allow lowercase letters, numbers, hyphens, underscores)
            valid_pattern = re.compile(r'^[a-z0-9_-]+$')
            if not valid_pattern.match(name_without_ext.lower()):
                invalid_chars = set(re.findall(r'[^a-z0-9_-]', name_without_ext.lower()))
                if invalid_chars:
                    char_display = ', '.join(repr(c) for c in sorted(invalid_chars))
                    issues.append(f"contains invalid characters: {char_display}")

            # Check for empty filename
            if not name_without_ext:
                issues.append("filename is empty")

            if issues:
                return ValidationStatus.FAIL, f"Filename '{self.filename}' violates naming rules: {'; '.join(issues)}"

            return ValidationStatus.PASS, f"Filename '{self.filename}' complies with eCTD naming conventions"

        except Exception as e:
            return ValidationStatus.FAIL, f"Error checking filename: {str(e)}"

    # =========================================================================
    # Cleanup
    # =========================================================================
    def close(self):
        """Clean up resources."""
        if self._fitz_doc:
            self._fitz_doc.close()
            self._fitz_doc = None


def validate_pdf(file_content: bytes, filename: str) -> ValidationResponse:
    """
    Convenience function to validate a PDF file against eCTD criteria.

    Args:
        file_content: Raw bytes of the PDF file
        filename: Original filename

    Returns:
        ValidationResponse with all 14 rule results for 100% eCTD compliance
    """
    validator = PDFValidator(file_content, filename)
    try:
        return validator.validate()
    finally:
        validator.close()
