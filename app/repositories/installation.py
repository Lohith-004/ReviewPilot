from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.installation import Installation


def get_installation(
    db: Session,
    github_installation_id: int,
) -> Installation | None:
    """
    Find an installation by its GitHub installation ID.
    """

    statement = select(Installation).where(
        Installation.github_installation_id == github_installation_id
    )

    return db.execute(statement).scalar_one_or_none()


def create_installation(
    db: Session,
    github_installation_id: int,
    account_login: str,
    account_type: str,
) -> Installation:
    """
    Create and persist a GitHub App installation.
    """

    installation = Installation(
        github_installation_id=github_installation_id,
        account_login=account_login,
        account_type=account_type,
    )

    db.add(installation)
    db.commit()
    db.refresh(installation)

    return installation