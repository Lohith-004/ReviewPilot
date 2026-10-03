
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
    token = await create_installation_access_token(167303229)

    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_get_installation_details():
    data = await get_installation_details(167303229)


    assert isinstance(data, dict)
    assert data["id"] == 167303229
    assert "account" in data

