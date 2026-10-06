from langfuse import propagate_attributes

from app.schemas.review import ReviewResult
from app.services.diff_processor import build_diff_chunks
from app.services.github_pull_request import get_pull_request_files
from app.services.llm_reviewer import LLMReviewer
from app.services.observability import get_langfuse_client


async def review_pull_request(
    installation_id: int,
    owner: str,
    repo: str,
    pull_request_number: int,
) -> list[ReviewResult]:
    """
    Fetch a pull request, process its diff, and review each chunk with Gemini.

    Langfuse records the review pipeline metadata without storing the full
    pull request diff.
    """

    langfuse = get_langfuse_client()

    if langfuse is None:
        return await _run_review_pipeline(
            installation_id=installation_id,
            owner=owner,
            repo=repo,
            pull_request_number=pull_request_number,
        )

    with langfuse.start_as_current_observation(
        name="review-pull-request",
        as_type="span",
        metadata={
            "repository": f"{owner}/{repo}",
            "pull_request_number": pull_request_number,
            "installation_id": installation_id,
        },
    ) as trace:
        with propagate_attributes(
            trace_name="review-pull-request",
            metadata={
                "repository": f"{owner}/{repo}",
                "pull_request_number": pull_request_number,
            },
        ):
            results = await _run_review_pipeline(
                installation_id=installation_id,
                owner=owner,
                repo=repo,
                pull_request_number=pull_request_number,
            )

        trace.update(
            output={
                "finding_count": sum(
                    len(result.findings)
                    for result in results
                ),
                "reviewed_chunks": len(results),
            }
        )

        langfuse.flush()

        return results


async def _run_review_pipeline(
    installation_id: int,
    owner: str,
    repo: str,
    pull_request_number: int,
) -> list[ReviewResult]:
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