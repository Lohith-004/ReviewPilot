from unittest.mock import AsyncMock, patch

from app.workers.review_worker import process_review_job


def test_process_review_job():
    mock_result = type(
        "MockReviewResult",
        (),
        {"findings": [object(), object()]},
    )()

    with patch(
        "app.workers.review_worker.review_pull_request",
        new=AsyncMock(return_value=[mock_result]),
    ) as mock_review:
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

    assert result == {
        "repository": "Lohith-004/ReviewPilot",
        "pull_request_number": 1,
        "chunks_reviewed": 1,
        "findings": 2,
    }