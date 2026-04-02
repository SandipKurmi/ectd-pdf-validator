# eCTD PDF Validation — What We Check and Why

This document explains all 14 validation rules the eCTD PDF Validator runs on every uploaded PDF.
Each rule maps directly to FDA/ICH eCTD submission requirements.

---

## Quick Overview

| Rule | Name | What It Checks |
|------|------|----------------|
| PDF_001 | PDF Version & Prohibited Content | Version number, no JavaScript/multimedia/attachments |
| PDF_002 | Document Integrity | File opens correctly, text is searchable |
| PDF_003 | Security Settings | No passwords or encryption |
| PDF_004 | Fast Web View | File is optimized for online viewing |
| PDF_005 | Bookmarks Integrity | Bookmarks point to real pages inside the document |
| PDF_006 | Hyperlinks Compliance | Links are internal-only and not broken |
| PDF_007 | Initial View & Layout | Correct panel opens when document is first opened |
| PDF_008 | Zoom Inheritance | Links and bookmarks don't force a fixed zoom level |
| PDF_009 | Font Embedding | All fonts are baked into the file |
| PDF_010 | Page Size | All pages are 8.5" × 11" (US Letter) |
| PDF_011 | Page Margins | Left margin is at least 0.75 inches |
| PDF_012 | Annotations | No sticky notes, highlights, or markups |
| PDF_013 | Image-Based Content | Document is not a scanned image dump |
| PDF_014 | File Naming | Filename uses only lowercase letters, numbers, hyphens, underscores |

---

## Detailed Rules

---

### PDF_001 — PDF Version & Prohibited Content

**What we check:**
- PDF version must be **1.4, 1.5, 1.6, or 1.7** (PDF/A-1 and PDF/A-2 also accepted)
- No **JavaScript** of any kind (document-level, page-level, form fields)
- No **multimedia** (audio, video, animations)
- No **embedded file attachments**
- No **3D content**

**Why:** The FDA requires a stable, widely-supported PDF format. Active content like JavaScript or multimedia creates security and compatibility risks.

**Examples:**

| Filename | Version | Result | Reason |
|----------|---------|--------|--------|
| `study-report.pdf` | 1.6 | PASS | Supported version, no active content |
| `interactive-form.pdf` | 1.7 + JS | FAIL | Contains JavaScript in form fields |
| `presentation.pdf` | 2.0 | FAIL | PDF 2.0 is not an allowed version |
| `media-rich.pdf` | 1.6 + video | FAIL | Contains embedded video |

---

### PDF_002 — Document Integrity

**What we check:**
- File opens without errors (not corrupted)
- Document has at least one page
- Text can be extracted (document is searchable)

**Why:** A corrupted or image-only document cannot be reviewed, searched, or processed by FDA systems.

**Examples:**

| File | Result | Reason |
|------|--------|--------|
| Normal readable PDF | PASS | Opens fine, text extracted successfully |
| Truncated/damaged PDF | FAIL | File cannot be opened |
| Scanned image with no OCR | FAIL | No extractable text found |

---

### PDF_003 — Security Settings

**What we check:**
- No **password protection** (open password or permissions password)
- No **encryption** that prevents printing or text selection

**Why:** FDA reviewers must be able to open, print, and copy text without any restrictions.

**Examples:**

| File | Result | Reason |
|------|--------|--------|
| Unprotected PDF | PASS | No encryption found |
| PDF with "owner password" | FAIL | Encryption restricts permissions |
| PDF requiring password to open | FAIL | Password-protected |

---

### PDF_004 — Fast Web View

**What we check:**
- The PDF is **linearized** (optimized for page-at-a-time web loading)

**Why:** eCTD submissions are reviewed online. A linearized PDF loads page by page so reviewers don't have to wait for the entire file to download before reading page 1.

**How to fix if failing:** In Adobe Acrobat, use **File → Save As → Optimized PDF** and enable "Fast Web View."

**Examples:**

| File | Result | Reason |
|------|--------|--------|
| Acrobat-optimized PDF | PASS | `/Linearized` marker found in file header |
| Exported from Word directly | FAIL | Not linearized |

---

### PDF_005 — Bookmarks Integrity

**What we check:**
- No **broken bookmarks** (pointing to a page that doesn't exist)
- No **external bookmarks** (pointing to another file or a website URL)
- All bookmarks stay within the current document

**Why:** External or broken bookmarks break navigation for FDA reviewers and are prohibited by eCTD spec.

**Examples:**

| Bookmark | Result | Reason |
|----------|--------|--------|
| "Section 2.1" → Page 15 (exists) | PASS | Valid internal reference |
| "Appendix A" → Page 200 (doc has 180 pages) | FAIL | Broken — page doesn't exist |
| "Reference" → `https://example.com` | FAIL | External URL not allowed |

---

### PDF_006 — Hyperlinks Compliance

**What we check:**
- No **external hyperlinks** (no `http://`, `https://`, `mailto:`, `ftp://` links)
- No **broken internal links** (pointing to a page that doesn't exist)
- No **launch actions** (links that open other programs)
- No **multiple-action links** (links with action chains)

**Why:** eCTD documents must be self-contained. External links can break over time and introduce security risks.

**Examples:**

| Link | Result | Reason |
|------|--------|--------|
| Jump to Page 5 (internal) | PASS | Valid internal navigation |
| `https://clinicaltrials.gov/...` | FAIL | External URL not allowed |
| Link to non-existent page 99 | FAIL | Broken link |

---

### PDF_007 — Initial View & Layout

**What we check:**
- If the document has bookmarks: it must open with the **Bookmarks Panel and Page** view
- If no bookmarks: it must open with **Page Only** view
- Document must **not** open in Full Screen mode

**Why:** Consistent opening behavior ensures reviewers see navigation immediately and aren't surprised by unusual display modes.

**Examples:**

| Document | Bookmarks? | Opens As | Result |
|----------|------------|----------|--------|
| Study report with TOC | Yes | Bookmarks Panel + Page | PASS |
| Simple cover letter | No | Page Only | PASS |
| Any document | — | Full Screen | FAIL |

---

### PDF_008 — Zoom Inheritance

**What we check:**
- Bookmarks and hyperlinks must use **"Inherit Zoom"** — they should not force a specific zoom level when clicked

**Why:** Different reviewers use different screen sizes. Forcing a fixed zoom level (like 150%) overrides the reviewer's preferred view.

**Examples:**

| Destination Setting | Result | Reason |
|--------------------|--------|--------|
| Jump to page, zoom = null (inherit) | PASS | Respects user's zoom preference |
| Jump to page, zoom = 150% (explicit) | FAIL | Forces a fixed zoom level |

---

### PDF_009 — Font Embedding

**What we check:**
- All **non-standard fonts** must be **fully embedded** in the file
- Standard PDF fonts (Times, Helvetica, Courier, Symbol, ZapfDingbats) don't need embedding

**Why:** If a font isn't embedded, the document looks different (or broken) on systems that don't have that font installed. eCTD requires consistent rendering.

**Examples:**

| Font Used | Embedded? | Result | Reason |
|-----------|-----------|--------|--------|
| Helvetica (standard) | N/A | PASS | Standard font, always available |
| Calibri (custom) | Yes | PASS | Non-standard but embedded |
| Calibri (custom) | No | FAIL | Non-standard font not embedded |

---

### PDF_010 — Page Size

**What we check:**
- Every page must be **8.5" × 11" (US Letter)** — portrait or landscape both accepted
- Tolerance: ±5 points (about 0.07 inches)

**Why:** eCTD requires US Letter format for consistent printing and archival.

**Examples:**

| Page Size | Result | Reason |
|-----------|--------|--------|
| 8.5" × 11" portrait | PASS | Standard letter size |
| 11" × 8.5" landscape | PASS | Letter landscape is acceptable |
| 8.27" × 11.69" (A4) | FAIL | A4 is not US Letter |
| 11" × 17" (Tabloid) | FAIL | Wrong size |

---

### PDF_011 — Page Margins

**What we check:**
- The **left margin** must be at least **0.75 inches** (54 points) on every page
- Checks the actual position of text, images, and drawings — not just the declared margin setting

**Why:** eCTD documents are often printed and bound. Content too close to the left edge gets obscured by the binding.

**Examples:**

| Left Content Start | Result | Reason |
|-------------------|--------|--------|
| 1.0" from left edge | PASS | Exceeds 0.75" minimum |
| 0.5" from left edge | FAIL | Insufficient margin |

---

### PDF_012 — Annotations

**What we check:**
- No **sticky notes**, highlights, underlines, strikethroughs, stamps, or any reviewer markup
- **Link annotations are allowed** (needed for navigation)
- Prohibited types include: Text, FreeText, Highlight, Underline, Stamp, Ink, Redact, Widget (form fields), and more

**Why:** Annotations are review artifacts and should not be in final submissions. They can obscure content and represent an incomplete document state.

**Examples:**

| Annotation | Result | Reason |
|------------|--------|--------|
| Navigation link (internal) | PASS | Link annotations are allowed |
| Yellow highlight on text | FAIL | Highlight annotation prohibited |
| Sticky note comment | FAIL | Text annotation prohibited |
| Redaction box | FAIL | Redact annotation prohibited |

---

### PDF_013 — Image-Based Content

**What we check:**
- If **more than 50%** of pages contain only images (no extractable text) → **FAIL**
- If **20–50%** of pages are image-only → **WARNING**
- Below 20% → **PASS**

**Why:** Scanned PDFs are harder to search, lower quality, and may not meet eCTD text-searchability requirements. Electronic source documents are strongly preferred.

**Examples:**

| Document Type | Image-Only Pages | Result |
|---------------|-----------------|--------|
| Word export to PDF | 0% | PASS |
| Mixed doc (some scanned figures) | 15% | PASS |
| Partially scanned document | 30% | WARNING |
| Fully scanned (no OCR) | 100% | FAIL |

---

### PDF_014 — File Naming

**What we check:**
- Filename must be **all lowercase**
- Only **letters (a–z), numbers (0–9), hyphens (`-`), and underscores (`_`)** are allowed
- No spaces, dots (except `.pdf`), or special characters

**Why:** eCTD submission systems are case-sensitive. Inconsistent naming can cause files to be unrecognized or rejected.

**Examples:**

| Filename | Result | Reason |
|----------|--------|--------|
| `clinical-study-report.pdf` | PASS | Lowercase, valid characters |
| `module3_section2.pdf` | PASS | Underscore is allowed |
| `Clinical Study Report.pdf` | FAIL | Uppercase letters and spaces |
| `report(final).pdf` | FAIL | Parentheses are not allowed |
| `Report_V2.pdf` | FAIL | Uppercase letters |

---

## How Results Are Reported

Each rule returns one of three statuses:

| Status | Meaning |
|--------|---------|
| **PASS** | Rule fully satisfied |
| **WARNING** | Potential issue — review recommended but not a hard failure |
| **FAIL** | Rule violated — submission will be rejected |

The overall document status is **FAIL** if any single rule fails.

---

*Generated: April 2, 2026 — eCTD PDF Validator v1.0*
