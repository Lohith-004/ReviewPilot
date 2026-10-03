import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings


client = TestClient(app)


def create_signature(payload: bytes) -> str:
    digest = hmac.new(
        settings.github_webhook_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={digest}"


def test_github_webhook_valid_signature():
    payload = {
        "action": "opened",
        "number": 42,
        "installation": {
            "id": 167303229
        },
        "pull_request": {
            "number": 42,
            "title": "Test PR",
            "user": {
                "login": "Lohith-004"
            },
            "head": {
                "sha": "abc123head"
            },
            "base": {
                "sha": "def456base"
            }
        },
    "repository": {
        "name": "ReviewPilot",
        "full_name": "Lohith-004/ReviewPilot"
        }
    }

    body = json.dumps(payload).encode("utf-8")

    response = client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-123",
            "X-Hub-Signature-256": create_signature(body),
        },
    )

    assert response.status_code == 202

    data = response.json()

    assert data["status"] == "accepted"
    assert data["event"] == "pull_request"
    assert data["delivery_id"] == "test-delivery-123"
    assert data["action"] == "opened"
    assert data["installation_id"] == 167303229
    assert data["repository"] == "Lohith-004/ReviewPilot"
    assert data["pr_number"] == 42
    assert data["pr_title"] == "Test PR"
    assert data["author"] == "Lohith-004"
    assert data["head_sha"] == "abc123head"
    assert data["base_sha"] == "def456base"


def test_github_webhook_invalid_signature():
    body = b'{"action":"opened","number":42}'

    response = client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=invalid",
        },
    )

    assert response.status_code == 403


def test_github_webhook_missing_signature():
    body = b'{"action":"opened","number":42}'

    response = client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "pull_request",
        },
    )

    assert response.status_code == 403