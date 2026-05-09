# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

This repo uses two virtualenvs that already exist on disk: `venv/` and `.venv/`. Either works; `venv/bin/uvicorn` is what the README uses.

```bash
# Install deps (into the active venv)
pip install -r requirements.txt

# Run dev server (reload on change)
venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# or:
python -m app.main

# Run via Docker
docker-compose up -d --build
docker-compose down
docker-compose logs -f
```

There is no test suite, linter, or formatter configured. If asked to add one, confirm choice with the user before introducing tooling.

Interactive API docs: `http://localhost:8000/docs` (Swagger) and `/redoc`.

## Architecture

Single-purpose FastAPI service that validates a PDF against the FDA eCTD PDF Properties Validation Criteria. The entire validation pipeline runs in-memory in one request — there is no database, no queue, no persistence.

**Request flow:** `app/main.py` mounts the router → `app/api/validate.py` (`POST /api/validate/pdf`) handles upload, enforces the 100 MB cap, checks the `%PDF-` signature, then calls `validate_pdf(file_content, filename)` from `app/services/pdf_validator.py`. The response shape is defined by Pydantic models in `app/models/response.py` (note the `populate_by_name` aliases — JSON uses camelCase like `ruleId`/`fileName`, Python uses snake_case).

**Validator design** (`app/services/pdf_validator.py`, ~1200 lines, the heart of the service):

- `PDFValidator` is instantiated per request with the raw bytes + filename. It lazy-loads two parsers and caches them: PyMuPDF (`fitz`) via `_get_fitz_document()` and PyPDF2 via `_get_pypdf_reader()`. Most rules use `fitz`; PyPDF2 is used where its API is more direct (e.g. encryption metadata). If either parser raises during load, `_is_corrupted` is set and dependent rules return FAIL with the cached corruption message rather than re-raising.
- Rules are dispatched from a single ordered list inside `validate()` — 14 rules (`PDF_001`–`PDF_014`) covering the 25 official eCTD criteria. To add or change a rule, edit that list AND the matching `_check_*` method; the rule ID/name string in the dispatch list is what appears in the JSON response.
- Each rule method returns `Tuple[ValidationStatus, str]`. `ValidationStatus` is `PASS | FAIL | WARNING`; the overall status is FAIL if **any** rule failed (warnings alone don't fail the run — see `validate()`).
- Class-level constants encode the spec: `ALLOWED_PDF_VERSIONS`, `LETTER_WIDTH_POINTS`/`LETTER_HEIGHT_POINTS` + `PAGE_SIZE_TOLERANCE`, `MIN_LEFT_MARGIN_POINTS`, `PROHIBITED_ANNOTATION_TYPES` (only `Link` is allowed), and the `IMAGE_BASED_THRESHOLD` / `IMAGE_WARNING_THRESHOLD` for PDF_013. Change these here, not inline in rule methods.

**Criteria → Rule mapping** is documented at the top of `pdf_validator.py` and in the README's coverage matrix; consult it before adding or renumbering rules so you don't double-cover or drop a criterion.

## Conventions worth preserving

- Response field names are camelCase on the wire (`ruleId`, `fileName`, `overallStatus`, `totalRules`) via Pydantic `alias=` — don't rename the JSON keys without checking API consumers.
- The `/` and `/health` endpoints both return the same `HealthResponse` and are used by Docker / load-balancer health checks.
