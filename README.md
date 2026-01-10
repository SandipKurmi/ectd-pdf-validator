# eCTD PDF Validator

A FastAPI-based validation service for checking PDF files against eCTD (Electronic Common Technical Document) PDF Properties Validation Criteria.

**100% eCTD Compliance Coverage** - Implements all 18 FDA eCTD PDF validation criteria through 14 comprehensive rules.

## Overview

This service provides enterprise-grade, rule-based PDF validation to ensure compliance with FDA eCTD submission requirements. It validates all required properties of PDF documents as specified in the official eCTD PDF Properties Validation Criteria checklist.

## Features

- **PDF Version & Content Validation**: PDF 1.4-1.7, PDF/A; no JavaScript, multimedia, 3D, or attachments
- **Document Integrity**: Verifies PDF readability and text searchability
- **Security Check**: Detects password protection and encryption restrictions
- **Fast Web View**: Validates linearization for optimized loading
- **Bookmarks Integrity**: No broken, external, or non-relative bookmarks
- **Hyperlinks Compliance**: No broken, external, multiple-action, or non-relative links
- **Initial View & Layout**: Correct PageMode (Bookmarks Panel or Page Only)
- **Zoom Inheritance**: All destinations use Inherit Zoom
- **Font Embedding**: All non-standard fonts fully embedded
- **Page Size**: 8.5" x 11" (US Letter) compliance
- **Page Margins**: Minimum 0.75" left margin for binding
- **Annotations Check**: No prohibited annotations (only Link allowed)
- **Image-Based Content**: Detects scanned/image-only PDFs
- **File Naming**: Lowercase with hyphens/underscores only

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

## Installation

1. Clone or navigate to the project directory:

```bash
cd ectd-pdf-validator
```

2. Create and activate a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Service

### Development Mode

```bash
venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or directly with Python:

```bash
python -m app.main
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The service will be available at `http://localhost:8000`

## API Documentation

Once the service is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check

```
GET /
```

Returns service health status.

**Response:**

```json
{
  "status": "UP",
  "service": "eCTD PDF Validator"
}
```

### PDF Validation

```
POST /api/validate/pdf
```

Validates a PDF file against all 14 eCTD compliance rules.

**Request:**

- Content-Type: `multipart/form-data`
- Body: `file` (PDF file, max 100MB)

**Example using curl:**

```bash
curl -X POST "http://localhost:8000/api/validate/pdf" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@study_report.pdf"
```

**Example using Python requests:**

```python
import requests

with open("study_report.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/validate/pdf",
        files={"file": f}
    )
    print(response.json())
```

**Response:**

```json
{
  "fileName": "study_report.pdf",
  "overallStatus": "PASS",
  "summary": {
    "totalRules": 14,
    "passed": 14,
    "failed": 0,
    "warnings": 0
  },
  "results": [
    {
      "ruleId": "PDF_001",
      "ruleName": "PDF Version & Prohibited Content",
      "status": "PASS",
      "message": "PDF version 1.7 is compliant with no prohibited content"
    },
    {
      "ruleId": "PDF_002",
      "ruleName": "Document Integrity",
      "status": "PASS",
      "message": "PDF is readable and text searchable (15420 characters extracted)"
    }
  ]
}
```

## Validation Rules (14 Rules - 100% eCTD Coverage)

| Rule ID | Rule Name                        | eCTD Criteria | Description                                                 |
| ------- | -------------------------------- | ------------- | ----------------------------------------------------------- |
| PDF_001 | PDF Version & Prohibited Content | 1-5           | PDF 1.4-1.7, no JavaScript, multimedia, 3D, attachments     |
| PDF_002 | Document Integrity               | 7-8           | Readable, text searchable                                   |
| PDF_003 | Security Settings                | 9             | No password protection or security restrictions             |
| PDF_004 | Fast Web View                    | 10            | PDF must be linearized                                      |
| PDF_005 | Bookmarks Integrity              | 16-17         | No broken, external, or non-relative bookmarks              |
| PDF_006 | Hyperlinks Compliance            | 12, 18-20     | No broken, external, multiple-action, or non-relative links |
| PDF_007 | Initial View & Layout            | 13-15         | Correct PageMode, layout, and magnification                 |
| PDF_008 | Zoom Inheritance                 | 11            | All destinations use Inherit Zoom                           |
| PDF_009 | Font Embedding                   | 21            | All non-standard fonts embedded                             |
| PDF_010 | Page Size                        | 22            | 8.5" x 11" (US Letter)                                      |
| PDF_011 | Page Margins                     | 23            | Minimum 0.75" left margin                                   |
| PDF_012 | Annotations                      | 6             | No prohibited annotations (only Link allowed)               |
| PDF_013 | Image-Based Content              | 24            | Avoid scanned/image-based PDFs                              |
| PDF_014 | File Naming                      | 25            | Lowercase, hyphens/underscores only                         |

## eCTD Criteria Coverage Matrix

| eCTD Criteria # | Description                           | Rule    |
| --------------- | ------------------------------------- | ------- |
| 1               | PDF Version 1.4-1.7, PDF/A-1, PDF/A-2 | PDF_001 |
| 2               | No JavaScript                         | PDF_001 |
| 3               | No dynamic content (multimedia)       | PDF_001 |
| 4               | No attachments                        | PDF_001 |
| 5               | No 3D content                         | PDF_001 |
| 6               | No PDF annotations                    | PDF_012 |
| 7               | File readable (not corrupted)         | PDF_002 |
| 8               | Text searchable                       | PDF_002 |
| 9               | No password/security                  | PDF_003 |
| 10              | Fast Web View (linearized)            | PDF_004 |
| 11              | Inherit Zoom                          | PDF_008 |
| 12              | No broken links                       | PDF_006 |
| 13              | Bookmark Panel & Page                 | PDF_007 |
| 14              | Page Layout = Default                 | PDF_007 |
| 15              | Magnification = Default               | PDF_007 |
| 16              | No external bookmarks                 | PDF_005 |
| 17              | No non-relative bookmarks             | PDF_005 |
| 18              | No external hyperlinks                | PDF_006 |
| 19              | No multiple action links              | PDF_006 |
| 20              | No non-relative hyperlinks            | PDF_006 |
| 21              | Fonts embedded                        | PDF_009 |
| 22              | Page size 8.5" x 11"                  | PDF_010 |
| 23              | Left margin >= 0.75"                  | PDF_011 |
| 24              | Avoid image-based PDFs                | PDF_013 |
| 25              | File naming conventions               | PDF_014 |

## Status Values

- **PASS**: Rule validation succeeded
- **FAIL**: Rule validation failed (critical issue - must fix before submission)
- **WARNING**: Rule validation passed with concerns (review recommended)

## Project Structure

```
ectd-pdf-validator/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── validate.py      # API routes
│   ├── services/
│   │   ├── __init__.py
│   │   └── pdf_validator.py # 14 validation rules
│   └── models/
│       ├── __init__.py
│       └── response.py      # Response schemas
├── requirements.txt
└── README.md
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Validation completed successfully
- `400 Bad Request`: Invalid file type, size, or format
- `500 Internal Server Error`: Unexpected processing error

## License

MIT License
