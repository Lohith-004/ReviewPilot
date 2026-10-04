from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.pull_request import PullRequestFile
from app.schemas.review import ReviewResult
from app.services.review_job import review_pull_request


@pytest.mark.asyncio
async def test_review_pull_request():
    files = [
        PullRequestFile(
            filename="app/main.py",
            status="modified",
            additions=2,
            deletions=1,
            changes=3,
            patch="""@@ -1,3 +1,4 @@
 def hello():
-    print("old")
+    print("new")
""",
        )
    ]

    expected_result = ReviewResult(findings=[])

    mock_reviewer = MagicMock()
    mock_reviewer.review = AsyncMock(
        return_value=expected_result
    )

    with patch(
        "app.services.review_job.get_pull_request_files",
        new_callable=AsyncMock,
        return_value=files,
    ) as mock_get_files:
        with patch(
            "app.services.review_job.LLMReviewer",
            return_value=mock_reviewer,
        ):
            results = await review_pull_request(
                installation_id=167303229,
                owner="Lohith-004",
                repo="ReviewPilot",
                pull_request_number=1,
            )

    assert len(results) == 1
    assert results[0].findings == []

    mock_get_files.assert_awaited_once_with(
        installation_id=167303229,
        owner="Lohith-004",
        repo="ReviewPilot",
        pull_request_number=1,
    )

    mock_reviewer.review.assert_awaited_once()