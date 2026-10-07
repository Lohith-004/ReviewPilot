import base64
from pathlib import Path
from time import time

import httpx
import jwt

from app.core.config import settings


def _load_private_key() -> str:
    """
    Load the GitHub App private key.

    Production deployments can provide the key as a base64-encoded
    environment variable. Local/Render deployments can provide a file path.
    """

    if settings.github_private_key_base64:
        try:
            return base64.b64decode(
                settings.github_private_key_base64
            ).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise RuntimeError(
                "Invalid GITHUB_PRIVATE_KEY_BASE64 value"
            ) from exc

    if settings.github_private_key_path:
        return Path(
            settings.github_private_key_path
        ).read_text()

    raise RuntimeError(
        "GitHub App private key is not configured. "
        "Set GITHUB_PRIVATE_KEY_BASE64 or "
        "GITHUB_PRIVATE_KEY_PATH."
    )


def create_github_app_jwt() -> str:
    """
    Create a short-lived JWT for authenticating as the GitHub App.
    """

    private_key = _load_private_key()

    now = int(time())

    payload = {
        "iat": now - 60,
        "exp": now + (10 * 60),
        "iss": str(settings.github_app_id),
    }

    return jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
    )


async def create_installation_access_token(
    installation_id: int,
) -> str:
    """
    Create a GitHub installation access token.
    """

    app_jwt = create_github_app_jwt()

    url = (
        f"https://api.github.com/app/installations/"
        f"{installation_id}/access_tokens"
    )

    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
        )

    response.raise_for_status()

    data = response.json()

    return data["token"]


async def get_installation_details(
    installation_id: int,
) -> dict:
    """
    Get details about a GitHub App installation.
    """

    app_jwt = create_github_app_jwt()

    url = (
        f"https://api.github.com/app/installations/"
        f"{installation_id}"
    )

    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=headers,
        )

    response.raise_for_status()

    return response.json()