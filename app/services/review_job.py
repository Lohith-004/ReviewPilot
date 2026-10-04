from app.schemas.review import ReviewResult
from app.services.diff_processor import build_diff_chunks
from app.services.github_pull_request import get_pull_request_files
from app.services.llm_reviewer import LLMReviewer


async def review_pull_request(
    installation_id: int,
    owner: str,
    repo: str,
    pull_request_number: int,
) -> list[ReviewResult]:
    """
    Fetch a pull request, process its diff, and review each chunk with Gemini.
    """

    files = await get_pull_request_files(
        installation_id=installation_id,
        owner=owner,
        repo=repo,
        pull_request_number=pull_request_number,
    )

    chunks = build_diff_chunks(files)

    reviewer = LLMReviewer()

    results: list[ReviewResult] = []

    for chunk in chunks:
        result = await reviewer.review(
            filename=chunk.filename,
            patch=chunk.patch,
        )

        results.append(result)

    return results