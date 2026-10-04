from enum import Enum

from pydantic import BaseModel, Field


class FindingSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingCategory(str, Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"


class ReviewFinding(BaseModel):
    file: str = Field(
        description="Path of the file containing the issue."
    )

    line: int = Field(
        description="Line number where the issue occurs."
    )

    severity: FindingSeverity = Field(
        description="Severity of the issue."
    )

    category: FindingCategory = Field(
        description="Category of the issue."
    )

    explanation: str = Field(
        description="Clear explanation of why this is a problem."
    )

    suggested_fix: str = Field(
        description="A concise suggested fix for the issue."
    )


class ReviewResult(BaseModel):
    findings: list[ReviewFinding] = Field(
        default_factory=list,
        description="List of genuine issues found in the code.",
    )