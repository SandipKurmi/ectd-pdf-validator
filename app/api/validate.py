"""
API Routes for PDF Validation.

This module defines the REST API endpoints for the eCTD PDF validation service.
All validation logic is delegated to the pdf_validator service.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.response import ValidationResponse, ErrorResponse
from app.services.pdf_validator import validate_pdf


# Create router with prefix and tags for OpenAPI documentation
router = APIRouter(prefix="/api/validate", tags=["validation"])

# Maximum file size: 100 MB (reasonable limit for eCTD PDF documents)
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_FILE_SIZE_MB = MAX_FILE_SIZE_BYTES / (1024 * 1024)


@router.post(
    "/pdf",
    response_model=ValidationResponse,
    responses={
        200: {"description": "Validation completed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid file type or size"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Validate PDF against eCTD criteria",
    description="""
    Validates an uploaded PDF file against eCTD PDF Properties Validation Criteria.

    The validation checks include:
    - PDF version compatibility (1.4-1.7, PDF/A-1, PDF/A-2)
    - Corruption and text searchability
    - Password protection and encryption
    - Fast Web View (linearization)
    - Bookmarks validation
    - Hyperlinks validation
    - Zoom and layout settings
    - Font embedding
    - Page size (8.5" x 11")
    - File naming conventions

    **Accepted file type:** PDF (.pdf)
    **Maximum file size:** 100 MB
    """,
)
async def validate_pdf_endpoint(
    file: UploadFile = File(..., description="PDF file to validate")
) -> ValidationResponse:
    """
    Validate a PDF file against eCTD compliance criteria.

    Args:
        file: The uploaded PDF file (multipart/form-data)

    Returns:
        ValidationResponse containing detailed validation results

    Raises:
        HTTPException: If file type is invalid or file size exceeds limit
    """
    # Validate file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only PDF files are accepted. Received: {file.filename}"
        )

    # Validate content type
    if file.content_type and file.content_type != "application/pdf":
        # Some clients may send different content types, so this is a soft check
        pass  # Allow but could add warning

    try:
        # Read file content
        file_content = await file.read()

        # Validate file size
        if len(file_content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE_MB:.0f} MB"
            )

        # Validate file is not empty
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )

        # Basic PDF signature check (PDF files start with %PDF-)
        if not file_content[:5].startswith(b'%PDF-'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file: File does not have valid PDF signature"
            )

        # Perform validation
        validation_result = validate_pdf(file_content, file.filename)

        return validation_result

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error in production
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the PDF: {str(e)}"
        )
    finally:
        # Ensure file handle is closed
        await file.close()
