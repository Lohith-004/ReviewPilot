from unittest.mock import AsyncMock, patch

from app.schemas.review import (
    FindingCategory,
    FindingSeverity,
    ReviewFinding,
)
from app.workers.review_worker import process_review_job


def test_process_review_job():
    mock_finding = ReviewFinding(
        file="app/auth.py",
        line=4,
        severity=FindingSeverity.HIGH,
        category=FindingCategory.SECURITY,
        explanation="Potential security vulnerability.",
        suggested_fix="Use a safer implementation.",
    )

    mock_result = type(
        "MockReviewResult",
        (),
        {"findings": [mock_finding, mock_finding]},
    )()

    with patch(
        "app.workers.review_worker.review_pull_request",
        new=AsyncMock(return_value=[mock_result]),
    ) as mock_review:

        with patch(
            "app.workers.review_worker.get_pull_request_details",
            new=AsyncMock(
                return_value={
                    "head_sha": "abc123head",
                }
            ),
        ) as mock_details:

            with patch(
                "app.workers.review_worker.create_pull_request_review",
                new=AsyncMock(
                    return_value={
                        "id": 12345,
                    }
                ),
            ) as mock_create_review:

                result = process_review_job(
                    installation_id=167303229,
                    owner="Lohith-004",
                    repo="ReviewPilot",
                    pull_request_number=1,
                )

    mock_review.assert_awaited_once_with(
        installation_id=167303229,
        owner="Lohith-004",
        repo="ReviewPilot",
        pull_request_number=1,
    )

    mock_details.assert_awaited_once_with(
        installation_id=167303229,
        owner="Lohith-004",
        repo="ReviewPilot",
        pull_request_number=1,
    )

    mock_create_review.assert_awaited_once()

    call = mock_create_review.await_args

    assert call.kwargs["commit_id"] == "abc123head"
    assert call.kwargs["owner"] == "Lohith-004"
    assert call.kwargs["repo"] == "ReviewPilot"
    assert call.kwargs["pull_request_number"] == 1
    assert len(call.kwargs["comments"]) == 2

    assert result == {
        "repository": "Lohith-004/ReviewPilot",
        "pull_request_number": 1,
        "chunks_reviewed": 1,
        "findings": 2,
        "review_id": 12345,
    }