import json

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import settings
from app.queue import review_queue
from app.schemas.github import PullRequestEvent
from app.services.github_webhook import verify_github_signature


router = APIRouter()


@router.post("/github", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
):
    payload = await request.body()

    is_valid = verify_github_signature(
        payload=payload,
        signature=x_hub_signature_256,
        secret=settings.github_webhook_secret,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook signature",
        )

    data = json.loads(payload)
    event = PullRequestEvent.model_validate(data)

    # Only process pull request events.
    if x_github_event != "pull_request":
        return {
            "status": "ignored",
            "event": x_github_event,
        }

    # Only review newly opened or updated pull requests.
    if event.action not in {"opened", "synchronize", "reopened"}:
        return {
            "status": "ignored",
            "event": x_github_event,
            "action": event.action,
        }

    owner, repo = event.repository.full_name.split("/", 1)

    job = review_queue.enqueue(
        "app.workers.review_worker.process_review_job",
        installation_id=event.installation.id,
        owner=owner,
        repo=repo,
        pull_request_number=event.number,
    )

    return {
        "status": "accepted",
        "event": x_github_event,
        "delivery_id": x_github_delivery,
        "action": event.action,
        "installation_id": event.installation.id,
        "repository": event.repository.full_name,
        "pr_number": event.number,
        "pr_title": event.pull_request.title,
        "author": event.pull_request.user.login,
        "head_sha": event.pull_request.head.sha,
        "base_sha": event.pull_request.base.sha,
        "job_id": job.id,
    }