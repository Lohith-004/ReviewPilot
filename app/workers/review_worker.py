import asyncio

from app.services.review_job import review_pull_request


def process_review_job(
    installation_id: int,
    owner: str,
    repo: str,
    pull_request_number: int,
):
    """
    RQ entry point for processing a GitHub pull request.
    """

    results = asyncio.run(
        review_pull_request(
            installation_id=installation_id,
            owner=owner,
            repo=repo,
            pull_request_number=pull_request_number,
        )
    )

    total_findings = sum(
        len(result.findings)
        for result in results
    )

    print(
        f"Review completed: "
        f"{owner}/{repo}#{pull_request_number} "
        f"with {total_findings} findings."
    )

    return {
        "repository": f"{owner}/{repo}",
        "pull_request_number": pull_request_number,
        "chunks_reviewed": len(results),
        "findings": total_findings,
    }