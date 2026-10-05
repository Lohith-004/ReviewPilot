from app.schemas.review import (
    FindingCategory,
    FindingSeverity,
    ReviewFinding,
)
from app.services.review_comments import build_github_review_comments


def test_build_github_review_comments():
    findings = [
        ReviewFinding(
            file="app/auth.py",
            line=4,
            severity=FindingSeverity.CRITICAL,
            category=FindingCategory.SECURITY,
            explanation="User input is directly concatenated into a SQL query.",
            suggested_fix="Use a parameterized query.",
        )
    ]

    comments = build_github_review_comments(findings)

    assert comments == [
        {
            "path": "app/auth.py",
            "line": 4,
            "side": "RIGHT",
            "body": (
                "**CRITICAL — Security**\n\n"
                "User input is directly concatenated into a SQL query.\n\n"
                "**Suggested fix:** Use a parameterized query."
            ),
        }
    ]