from sqlalchemy import text

from app.db.session import SessionLocal
from app.repositories.installation import (
    create_installation,
    get_installation,
)


def test_create_and_get_installation():
    db = SessionLocal()

    test_installation_id = 999999999

    try:
        installation = create_installation(
            db=db,
            github_installation_id=test_installation_id,
            account_login="test-user",
            account_type="User",
        )

        assert installation.github_installation_id == test_installation_id
        assert installation.account_login == "test-user"
        assert installation.account_type == "User"

        saved_installation = get_installation(
            db=db,
            github_installation_id=test_installation_id,
        )

        assert saved_installation is not None
        assert saved_installation.github_installation_id == test_installation_id
        assert saved_installation.account_login == "test-user"
        assert saved_installation.account_type == "User"

    finally:
        db.rollback()

        db.execute(
            text(
                """
                DELETE FROM installations
                WHERE github_installation_id = :installation_id
                """
            ),
            {"installation_id": test_installation_id},
        )

        db.commit()
        db.close()