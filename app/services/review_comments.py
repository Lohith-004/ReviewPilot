from app.schemas.review import ReviewFinding


def build_github_review_comments(
    findings: list[ReviewFinding],
) -> list[dict]:
    """
    Convert ReviewPilot findings into GitHub inline review comments.
    """

    comments = []

    for finding in findings:
        body = (
            f"**{finding.severity.value.upper()} — "
            f"{finding.category.value.replace('_', ' ').title()}**\n\n"
            f"{finding.explanation}\n\n"
            f"**Suggested fix:** {finding.suggested_fix}"
        )

        comments.append(
            {
                "path": finding.file,
                "line": finding.line,
                "side": "RIGHT",
                "body": body,
            }
        )

    return comments