from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.models.webhook_delivery import WebhookDelivery


def record_webhook_delivery(
    delivery_id: str,
    event: str,
    repository: str | None,
) -> bool:
    """
    Record a GitHub webhook delivery.

    Returns:
        True  -> delivery was recorded for the first time.
        False -> delivery was already processed.
    """
    db = SessionLocal()

    try:
        delivery = WebhookDelivery(
            delivery_id=delivery_id,
            event=event,
            repository=repository,
        )

        db.add(delivery)
        db.commit()

        return True

    except IntegrityError:
        db.rollback()
        return False

    finally:
        db.close()