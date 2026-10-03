from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.pull_request import PullRequestFile
from app.services.github_pull_request import get_pull_request_files


@pytest.mark.asyncio
async def test_get_pull_request_files():
    mock_response = MagicMock()

    mock_response.json.return_value = [
        {
            "filename": "app/main.py",
            "status": "modified",
            "additions": 5,
            "deletions": 2,
            "changes": 7,
            "patch": "@@ -1,3 +1,6 @@",
        }
    ]

    mock_response.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch(
        "app.services.github_pull_request.create_installation_access_token",
        new_callable=AsyncMock,
        return_value="test-access-token",
    ):
        with patch(
            "app.services.github_pull_request.httpx.AsyncClient"
        ) as mock_async_client:
            mock_async_client.return_value.__aenter__.return_value = (
                mock_client
            )

            files = await get_pull_request_files(
                installation_id=167303229,
                owner="Lohith-004",
                repo="ReviewPilot",
                pull_request_number=1,
            )

    assert len(files) == 1
    assert isinstance(files[0], PullRequestFile)

    assert files[0].filename == "app/main.py"
    assert files[0].status == "modified"
    assert files[0].additions == 5
    assert files[0].deletions == 2
    assert files[0].changes == 7
    assert files[0].patch == "@@ -1,3 +1,6 @@"

    mock_client.get.assert_awaited_once()