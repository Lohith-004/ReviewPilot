import httpx

from app.core.github_auth import create_installation_access_token


GITHUB_API_BASE = "https://api.github.com"


async def create_pull_request_review(
    installation_id: int,
    owner: str,
    repo: str,
    pull_request_number: int,
    commit_id: str,
    body: str,
    comments: list[dict],
) -> dict:
    """
    Create a GitHub pull request review with inline comments.
    """

    access_token = await create_installation_access_token(
        installation_id
    )

    url = (
        f"{GITHUB_API_BASE}/repos/"
        f"{owner}/{repo}/pulls/{pull_request_number}/reviews"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }

    payload = {
        "commit_id": commit_id,
        "body": body,
        "event": "COMMENT",
        "comments": comments,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            json=payload,
        )

    response.raise_for_status()

    return response.json()