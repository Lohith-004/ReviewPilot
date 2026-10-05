import asyncio

from app.services.github_pull_request import get_pull_request_details
from app.services.github_review import create_pull_request_review
from app.services.review_comments import build_github_review_comments
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

    async def run_review():
        results = await review_pull_request(
            installation_id=installation_id,
            owner=owner,
            repo=repo,
            pull_request_number=pull_request_number,
        )

        pr_details = await get_pull_request_details(
            installation_id=installation_id,
            owner=owner,
            repo=repo,
            pull_request_number=pull_request_number,
        )

        all_findings = []

        for result in results:
            all_findings.extend(result.findings)

        comments = build_github_review_comments(all_findings)

        review = None

        if comments:
            review = await create_pull_request_review(
                installation_id=installation_id,
                owner=owner,
                repo=repo,
                pull_request_number=pull_request_number,
                commit_id=pr_details["head_sha"],
                body=(
                    f"ReviewPilot found {len(all_findings)} "
                    f"potential issue(s) in this pull request."
                ),
                comments=comments,
            )

        return results, review

    results, review = asyncio.run(run_review())

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
        "review_id": review["id"] if review else None,
    }