import httpx

from app.core.github_auth import create_installation_access_token
from app.schemas.pull_request import PullRequestFile


GITHUB_API_BASE = "https://api.github.com"


async def get_pull_request_files(
    installation_id: int,
    owner: str,
    repo: str,
    pull_request_number: int,
) -> list[PullRequestFile]:
    """
    Fetch the files changed in a GitHub pull request.
    """

    access_token = await create_installation_access_token(
        installation_id
    )

    url = (
        f"{GITHUB_API_BASE}/repos/"
        f"{owner}/{repo}/pulls/{pull_request_number}/files"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=headers,
            params={"per_page": 100},
        )

    response.raise_for_status()

    data = response.json()

    return [
        PullRequestFile.model_validate(file)
        for file in data
    ]


async def get_pull_request_details(
    installation_id: int,
    owner: str,
    repo: str,
    pull_request_number: int,
) -> dict:
    """
    Fetch pull request metadata needed for publishing a review.
    """

    access_token = await create_installation_access_token(
        installation_id
    )

    url = (
        f"{GITHUB_API_BASE}/repos/"
        f"{owner}/{repo}/pulls/{pull_request_number}"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=headers,
        )

    response.raise_for_status()

    data = response.json()

    return {
        "head_sha": data["head"]["sha"],
    }