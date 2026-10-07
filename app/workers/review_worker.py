import asyncio
import logging
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


logger = logging.getLogger(__name__)


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

        logger.info(
            "Starting review pipeline for %s/%s#%s",
            owner,
            repo,
            pull_request_number,
        )

        details_start = time.perf_counter()

        pr_details = await get_pull_request_details(
            installation_id=installation_id,
            owner=owner,
            repo=repo,
            pull_request_number=pull_request_number,
        )

        logger.info(
            "PR details fetched in %.2fs",
            time.perf_counter() - details_start,
        )

        review_run = create_review_run(
            repository=f"{owner}/{repo}",
            pull_request_number=pull_request_number,
            commit_sha=pr_details["head_sha"],
        )

        logger.info(
            "Created review run id=%s status=%s",
            review_run.id,
            review_run.status,
        )

        try:
            review_start = time.perf_counter()

            results = await review_pull_request(
                installation_id=installation_id,
                owner=owner,
                repo=repo,
                pull_request_number=pull_request_number,
            )

            logger.info(
                "Diff + Gemini stage completed in %.2fs",
                time.perf_counter() - review_start,
            )

            all_findings = []

            for result in results:
                all_findings.extend(result.findings)

            logger.info(
                "Total findings collected: %s",
                len(all_findings),
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

                logger.info(
                    "GitHub review posted in %.2fs",
                    time.perf_counter() - review_start,
                )
            else:
                logger.info(
                    "No findings. Skipping GitHub review."
                )

            complete_review_run(
                review_run_id=review_run.id,
                findings=all_findings,
            )

            logger.info(
                "Review run %s marked completed with %s findings",
                review_run.id,
                len(all_findings),
            )

            logger.info(
                "Total pipeline time: %.2fs",
                time.perf_counter() - pipeline_start,
            )

            return results, review

        except Exception:
            fail_review_run(review_run.id)

            logger.exception(
                "Review run %s failed",
                review_run.id,
            )

            raise

    results, review = asyncio.run(run_review())

    total_findings = sum(
        len(result.findings)
        for result in results
    )

    logger.info(
        "Review completed for %s/%s#%s with %s findings",
        owner,
        repo,
        pull_request_number,
        total_findings,
    )

    return {
        "repository": f"{owner}/{repo}",
        "pull_request_number": pull_request_number,
        "chunks_reviewed": len(results),
        "findings": total_findings,
        "review_id": review["id"] if review else None,
    }