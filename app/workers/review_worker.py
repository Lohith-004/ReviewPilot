import asyncio
import time

from app.services.github_pull_request import get_pull_request_details
from app.services.github_review import create_pull_request_review
from app.services.review_comments import build_github_review_comments
from app.services.review_job import review_pull_request
from app.services.review_persistence import (
    complete_review_run,
    create_review_run,
    fail_review_run,
)


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
        pipeline_start = time.perf_counter()

        print(
            f"[WORKER] Starting review pipeline: "
            f"{owner}/{repo}#{pull_request_number}"
        )

        details_start = time.perf_counter()

        pr_details = await get_pull_request_details(
            installation_id=installation_id,
            owner=owner,
            repo=repo,
            pull_request_number=pull_request_number,
        )

        print(
            f"[WORKER] PR details fetched "
            f"in {time.perf_counter() - details_start:.2f}s"
        )

        review_run = create_review_run(
            repository=f"{owner}/{repo}",
            pull_request_number=pull_request_number,
            commit_sha=pr_details["head_sha"],
        )

        print(
            f"[DB] Created review run "
            f"id={review_run.id} status={review_run.status}"
        )

        try:
            review_start = time.perf_counter()

            results = await review_pull_request(
                installation_id=installation_id,
                owner=owner,
                repo=repo,
                pull_request_number=pull_request_number,
            )

            print(
                f"[WORKER] Diff + Gemini stage completed "
                f"in {time.perf_counter() - review_start:.2f}s"
            )

            all_findings = []

            for result in results:
                all_findings.extend(result.findings)

            print(
                f"[WORKER] Total findings collected: "
                f"{len(all_findings)}"
            )

            comments = build_github_review_comments(all_findings)

            review = None

            if comments:
                review_start = time.perf_counter()

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

                print(
                    f"[WORKER] GitHub review posted "
                    f"in {time.perf_counter() - review_start:.2f}s"
                )
            else:
                print(
                    "[WORKER] No findings. "
                    "Skipping GitHub review."
                )

            complete_review_run(
                review_run_id=review_run.id,
                findings=all_findings,
            )

            print(
                f"[DB] Review run {review_run.id} "
                f"marked completed with "
                f"{len(all_findings)} findings"
            )

            print(
                f"[WORKER] Total pipeline time: "
                f"{time.perf_counter() - pipeline_start:.2f}s"
            )

            return results, review

        except Exception:
            fail_review_run(review_run.id)

            print(
                f"[DB] Review run {review_run.id} "
                "marked failed"
            )

            raise

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