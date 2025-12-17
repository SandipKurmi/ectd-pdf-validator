"""
eCTD PDF Validator - FastAPI Application Entry Point.

This service validates PDF files against eCTD (Electronic Common Technical Document)
PDF Properties Validation Criteria using rule-based logic.

The service provides:
- Health check endpoint for monitoring
- PDF validation endpoint for eCTD compliance checking
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.validate import router as validate_router
from app.models.response import HealthResponse


# Application metadata for OpenAPI documentation
app = FastAPI(
    title="eCTD PDF Validator",
    description="""
    A validation service for checking PDF files against eCTD PDF Properties Validation Criteria.

    ## Features
    - PDF version validation (1.4-1.7, PDF/A)
    - Corruption and text searchability checks
    - Password protection detection
    - Fast Web View (linearization) verification
    - Bookmarks validation
    - Hyperlinks compliance checking
    - Zoom and layout settings verification
    - Font embedding validation
    - Page size validation (8.5" x 11")
    - File naming convention checks

    ## Usage
    Upload a PDF file to the `/api/validate/pdf` endpoint to receive a comprehensive
    validation report with individual rule results.
    """,
    version="1.0.0",
    contact={
        "name": "API Support",
    },
    license_info={
        "name": "MIT",
    },
)

# Configure CORS for development and production use
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include validation routes
app.include_router(validate_router)


@app.get(
    "/",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check endpoint",
    description="Returns the service health status. Use this endpoint for monitoring and load balancer health checks.",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse indicating service status
    """
    return HealthResponse(
        status="UP",
        service="eCTD PDF Validator"
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check endpoint (alias)",
    description="Alias for the root health check endpoint.",
)
async def health_check_alias() -> HealthResponse:
    """
    Alternative health check endpoint.

    Returns:
        HealthResponse indicating service status
    """
    return HealthResponse(
        status="UP",
        service="eCTD PDF Validator"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload for development
    )
