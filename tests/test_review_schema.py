from app.schemas.review import (
    FindingCategory,
    FindingSeverity,
    ReviewFinding,
    ReviewResult,
)


def test_review_finding():
    finding = ReviewFinding(
        file="app/main.py",
        line=42,
        severity=FindingSeverity.HIGH,
        category=FindingCategory.BUG,
        explanation="The function can access an undefined variable.",
        suggested_fix="Initialize the variable before using it.",
    )

    assert finding.file == "app/main.py"
    assert finding.line == 42
    assert finding.severity == FindingSeverity.HIGH
    assert finding.category == FindingCategory.BUG


def test_review_result_with_findings():
    finding = ReviewFinding(
        file="app/main.py",
        line=10,
        severity=FindingSeverity.MEDIUM,
        category=FindingCategory.CODE_QUALITY,
        explanation="This logic is duplicated.",
        suggested_fix="Extract the duplicated logic into a helper function.",
    )

    result = ReviewResult(findings=[finding])

    assert len(result.findings) == 1
    assert result.findings[0].file == "app/main.py"


def test_review_result_can_be_empty():
    result = ReviewResult()

    assert result.findings == []