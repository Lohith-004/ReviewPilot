from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.github_review import create_pull_request_review


@pytest.mark.asyncio
async def test_create_pull_request_review():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": 12345,
        "body": "Review completed",
    }
    mock_response.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch(
        "app.services.github_review.create_installation_access_token",
        new_callable=AsyncMock,
        return_value="test-access-token",
    ) as mock_token:
        with patch(
            "app.services.github_review.httpx.AsyncClient"
        ) as mock_async_client:

            mock_async_client.return_value.__aenter__.return_value = mock_client

            result = await create_pull_request_review(
                installation_id=167303229,
                owner="Lohith-004",
                repo="ReviewPilot",
                pull_request_number=1,
                commit_id="abc123",
                body="Review completed",
                comments=[
                    {
                        "path": "app/auth.py",
                        "line": 4,
                        "side": "RIGHT",
                        "body": "Potential SQL injection vulnerability.",
                    }
                ],
            )

    mock_token.assert_awaited_once_with(167303229)

    mock_client.post.assert_awaited_once()

    call = mock_client.post.await_args

    assert call.kwargs["headers"]["Authorization"] == (
        "Bearer test-access-token"
    )

    assert call.kwargs["json"] == {
        "commit_id": "abc123",
        "body": "Review completed",
        "event": "COMMENT",
        "comments": [
            {
                "path": "app/auth.py",
                "line": 4,
                "side": "RIGHT",
                "body": "Potential SQL injection vulnerability.",
            }
        ],
    }

    assert result == {
        "id": 12345,
        "body": "Review completed",
    }