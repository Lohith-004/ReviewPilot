from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.github_pull_request import get_pull_request_details


@pytest.mark.asyncio
async def test_get_pull_request_details():
    mock_response = MagicMock()

    mock_response.json.return_value = {
        "head": {
            "sha": "abc123head",
        }
    }

    mock_response.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch(
        "app.services.github_pull_request.create_installation_access_token",
        new_callable=AsyncMock,
        return_value="test-access-token",
    ) as mock_token:
        with patch(
            "app.services.github_pull_request.httpx.AsyncClient"
        ) as mock_async_client:

            mock_async_client.return_value.__aenter__.return_value = (
                mock_client
            )

            result = await get_pull_request_details(
                installation_id=167303229,
                owner="Lohith-004",
                repo="ReviewPilot",
                pull_request_number=1,
            )

    mock_token.assert_awaited_once_with(167303229)

    mock_client.get.assert_awaited_once()

    assert result == {
        "head_sha": "abc123head",
    }