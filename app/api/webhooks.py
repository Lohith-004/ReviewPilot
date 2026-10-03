import json

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import settings
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

    return {
        "status": "accepted",
        "event": x_github_event,
        "delivery_id": x_github_delivery,
        "action": data.get("action"),
    }