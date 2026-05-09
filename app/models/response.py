"""
Response models for the eCTD PDF Validator API.

These Pydantic models define the structure of API responses,
ensuring consistent and well-documented output formats.
"""

from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    """Enumeration of possible validation statuses for individual rules."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    INFORMATION = "INFORMATION"


class OverallStatus(str, Enum):
    """Enumeration of possible overall validation statuses."""
    PASS = "PASS"
    FAIL = "FAIL"


class RuleResult(BaseModel):
    """
    Result of a single validation rule check.

    Attributes:
        rule_id: Unique identifier for the rule (e.g., PDF_001)
        rule_name: Human-readable name of the rule
        status: Whether the rule passed, failed, or generated a warning
        message: Detailed explanation of the result
    """
    rule_id: str = Field(..., alias="ruleId", description="Unique rule identifier")
    rule_name: str = Field(..., alias="ruleName", description="Human-readable rule name")
    status: ValidationStatus = Field(..., description="Validation status")
    message: str = Field(..., description="Detailed result message")

    class Config:
        populate_by_name = True


class ValidationSummary(BaseModel):
    """
    Summary statistics for the validation run.

    Attributes:
        total_rules: Total number of rules checked
        passed: Number of rules that passed
        failed: Number of rules that failed
        warnings: Number of rules that generated warnings
    """
    total_rules: int = Field(..., alias="totalRules", description="Total rules checked")
    passed: int = Field(..., description="Number of passed rules")
    failed: int = Field(..., description="Number of failed rules")
    warnings: int = Field(..., description="Number of warnings")
    information: int = Field(..., description="Number of informational rules")

    class Config:
        populate_by_name = True


class ValidationResponse(BaseModel):
    """
    Complete validation response returned by the API.

    Attributes:
        file_name: Name of the validated PDF file
        overall_status: Overall validation result (PASS/FAIL)
        summary: Statistical summary of rule results
        results: List of individual rule results
    """
    file_name: str = Field(..., alias="fileName", description="Name of the validated file")
    overall_status: OverallStatus = Field(..., alias="overallStatus", description="Overall validation status")
    summary: ValidationSummary = Field(..., description="Summary of validation results")
    results: List[RuleResult] = Field(..., description="Individual rule results")

    class Config:
        populate_by_name = True


class HealthResponse(BaseModel):
    """
    Health check response model.

    Attributes:
        status: Service health status
        service: Service name
    """
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")


class ErrorResponse(BaseModel):
    """
    Error response model for API errors.

    Attributes:
        detail: Error description
    """
    detail: str = Field(..., description="Error description")
