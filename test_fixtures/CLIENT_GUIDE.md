# eCTD PDF Validator — Test Files Guide

This folder contains 15 sample PDF files. Each one is named by the rule it targets.
Upload any of these to `POST /api/validate/pdf` to see how the API responds.

## How to test

- **Browser:** open <http://localhost:8000/docs>, expand `POST /api/validate/pdf`, click **Try it out**, upload one of the files below.
- **curl:**

  ```bash
  curl -X POST http://localhost:8000/api/validate/pdf \
    -F "file=@test_fixtures/00_all_rules_pass.pdf"
  ```

## Status meanings

| Status        | Meaning                                                | Affects overall? |
| ------------- | ------------------------------------------------------ | ---------------- |
| `PASS`        | Rule satisfied.                                        | no               |
| `WARNING`     | Issue noted — not a hard failure.                      | no               |
| `INFORMATION` | Informational only — not a compliance failure.         | no               |
| `FAIL`        | Compliance failure. `overallStatus` becomes `FAIL`.    | **yes**          |

## Test files (one per rule + a complete-pass case)

| File                                    | Tests   | Expected rule status      | Expected overall |
| --------------------------------------- | ------- | ------------------------- | ---------------- |
| `00_all_rules_pass.pdf`                 | all 14  | every rule `PASS`         | **PASS**         |
| `01_pdf_version_old.pdf`                | PDF_001 | `WARNING` (version 1.2)   | PASS             |
| `02_short_text_only.pdf`                | PDF_002 | `FAIL` (text not searchable) | FAIL          |
| `03_password_protected.pdf`             | PDF_003 | `FAIL` (encrypted)        | FAIL             |
| `04_not_linearized.pdf`                 | PDF_004 | `FAIL` (no Fast Web View) | FAIL             |
| `05_external_bookmark.pdf`              | PDF_005 | `FAIL` (external bookmark) | FAIL            |
| `06_external_hyperlink.pdf`             | PDF_006 | `FAIL` (external link)    | FAIL             |
| `07_wrong_initial_view.pdf`             | PDF_007 | `FAIL` (wrong PageMode)   | FAIL             |
| `08_explicit_zoom_bookmarks.pdf`        | PDF_008 | `FAIL` (explicit zoom)    | FAIL             |
| `09_non_embedded_font.pdf`              | PDF_009 | `INFORMATION` (font not embedded) | PASS     |
| `10_a4_page_size.pdf`                   | PDF_010 | `INFORMATION` (A4 not Letter) | FAIL\*       |
| `11_narrow_left_margin.pdf`             | PDF_011 | `INFORMATION` (margin < 0.75") | FAIL\*      |
| `12_with_annotations.pdf`               | PDF_012 | `WARNING` (highlight + sticky note) | FAIL\* |
| `13_image_only_scan.pdf`                | PDF_013 | `FAIL` (scanned image)    | FAIL             |
| `14_BAD-Filename.pdf`                   | PDF_014 | `FAIL` (bad filename)     | FAIL             |

\* Files marked with an asterisk are designed to demonstrate one rule, but their `overallStatus` is `FAIL` only because of PDF_004 (Fast Web View). The PDF generator we use cannot produce linearized PDFs, so synthetic test files always fail PDF_004 in addition to their target rule. The two exceptions — `00_all_rules_pass.pdf`, `01_pdf_version_old.pdf`, `06_external_hyperlink.pdf`, and `09_non_embedded_font.pdf` — are real Acrobat-produced PDFs and are linearized.

## Quick rule reference

| Rule    | Name                              | Classification | Triggers FAIL? |
| ------- | --------------------------------- | -------------- | -------------- |
| PDF_001 | PDF Version & Prohibited Content  | warning        | no             |
| PDF_002 | Document Integrity                | invalid        | yes            |
| PDF_003 | Security Settings                 | invalid        | yes            |
| PDF_004 | Fast Web View                     | invalid        | yes            |
| PDF_005 | Bookmarks Integrity               | invalid        | yes            |
| PDF_006 | Hyperlinks Compliance             | invalid        | yes            |
| PDF_007 | Initial View & Layout             | invalid        | yes            |
| PDF_008 | Zoom Inheritance                  | invalid        | yes            |
| PDF_009 | Font Embedding                    | information    | no             |
| PDF_010 | Page Size                         | information    | no             |
| PDF_011 | Page Margins                      | information    | no             |
| PDF_012 | Annotations                       | warning        | no             |
| PDF_013 | Image-Based Content               | invalid        | yes            |
| PDF_014 | File Naming                       | invalid        | yes            |
