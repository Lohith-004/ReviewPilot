from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.models.review_finding import ReviewFinding
from app.models.review_run import ReviewRun
from app.schemas.review import ReviewFinding as ReviewFindingSchema


def create_review_run(
    repository: str,
    pull_request_number: int,
    commit_sha: str,
) -> ReviewRun:
    db = SessionLocal()

    try:
        review_run = ReviewRun(
            repository=repository,
            pull_request_number=pull_request_number,
            commit_sha=commit_sha,
            status="running",
            started_at=datetime.now(timezone.utc),
        )

        db.add(review_run)
        db.commit()
        db.refresh(review_run)

        return review_run
    finally:
        db.close()


def complete_review_run(
    review_run_id: int,
    findings: list[ReviewFindingSchema],
) -> None:
    db = SessionLocal()

    try:
        review_run = db.get(ReviewRun, review_run_id)

        if review_run is None:
            raise ValueError(
                f"Review run {review_run_id} does not exist."
            )

        for finding in findings:
            db.add(
                ReviewFinding(
                    review_run_id=review_run_id,
                    file=finding.file,
                    line=finding.line,
                    severity=finding.severity.value,
                    category=finding.category.value,
                    explanation=finding.explanation,
                    suggested_fix=finding.suggested_fix,
                )
            )

        review_run.status = "completed"
        review_run.completed_at = datetime.now(timezone.utc)

        db.commit()
    finally:
        db.close()


def fail_review_run(
    review_run_id: int,
) -> None:
    db = SessionLocal()

    try:
        review_run = db.get(ReviewRun, review_run_id)

        if review_run is None:
            raise ValueError(
                f"Review run {review_run_id} does not exist."
            )

        review_run.status = "failed"
        review_run.completed_at = datetime.now(timezone.utc)

        db.commit()
    finally:
        db.close()