from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.github_auth import (
    create_github_app_jwt,
    create_installation_access_token,
    get_installation_details,
)


def test_create_github_app_jwt():
    token = create_github_app_jwt()

    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_create_installation_access_token():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "token": "ghs_test_installation_token",
    }
    mock_response.raise_for_status.return_value = None

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_client)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "app.core.github_auth.httpx.AsyncClient",
        return_value=mock_context_manager,
    ), patch(
        "app.core.github_auth.create_github_app_jwt",
        return_value="test-app-jwt",
    ):

        token = await create_installation_access_token(167303229)

    assert token == "ghs_test_installation_token"

    mock_client.post.assert_awaited_once()

    call_args = mock_client.post.await_args

    assert (
        call_args.args[0]
        == "https://api.github.com/app/installations/"
        "167303229/access_tokens"
    )

    headers = call_args.kwargs["headers"]

    assert headers["Authorization"] == "Bearer test-app-jwt"
    assert headers["Accept"] == "application/vnd.github+json"
    assert headers["X-GitHub-Api-Version"] == "2026-03-10"


@pytest.mark.asyncio
async def test_get_installation_details():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": 167303229,
        "account": {
            "login": "Lohith-004",
            "type": "User",
        },
    }
    mock_response.raise_for_status.return_value = None

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_client)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "app.core.github_auth.httpx.AsyncClient",
        return_value=mock_context_manager,
    ), patch(
        "app.core.github_auth.create_github_app_jwt",
        return_value="test-app-jwt",
    ):

        data = await get_installation_details(167303229)

    assert isinstance(data, dict)
    assert data["id"] == 167303229
    assert "account" in data

    mock_client.get.assert_awaited_once()

    call_args = mock_client.get.await_args

    assert (
        call_args.args[0]
        == "https://api.github.com/app/installations/"
        "167303229"
    )

    headers = call_args.kwargs["headers"]

    assert headers["Authorization"] == "Bearer test-app-jwt"
    assert headers["Accept"] == "application/vnd.github+json"
    assert headers["X-GitHub-Api-Version"] == "2026-03-10"