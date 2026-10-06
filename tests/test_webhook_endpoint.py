import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


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
            "id": 167303229,
            "node_id": "MDIzOkludGVncmF0aW9uSW5zdGFsbGF0aW9uMTY3MzAzMjI5",
        },
        "pull_request": {
            "number": 42,
            "title": "Test PR",
            "user": {
                "login": "Lohith-004",
            },
            "head": {
                "sha": "abc123head",
            },
            "base": {
                "sha": "def456base",
            },
        },
        "repository": {
            "name": "ReviewPilot",
            "full_name": "Lohith-004/ReviewPilot",
        },
    }

    body = json.dumps(payload).encode("utf-8")

    mock_job = MagicMock()
    mock_job.id = "test-job-123"

    with patch(
        "app.api.webhooks.review_queue.enqueue",
        return_value=mock_job,
    ) as mock_enqueue, patch(
        "app.api.webhooks.record_webhook_delivery",
        return_value=True,
    ) as mock_record:

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
    assert data["job_id"] == "test-job-123"

    mock_record.assert_called_once_with(
        delivery_id="test-delivery-123",
        event="pull_request",
        repository="Lohith-004/ReviewPilot",
    )

    mock_enqueue.assert_called_once_with(
        "app.workers.review_worker.process_review_job",
        installation_id=167303229,
        owner="Lohith-004",
        repo="ReviewPilot",
        pull_request_number=42,
    )


def test_github_webhook_duplicate_delivery():
    payload = {
        "action": "opened",
        "number": 42,
        "installation": {
            "id": 167303229,
            "node_id": "test-node",
        },
        "pull_request": {
            "number": 42,
            "title": "Duplicate Test PR",
            "user": {
                "login": "Lohith-004",
            },
            "head": {
                "sha": "duplicate-head",
            },
            "base": {
                "sha": "duplicate-base",
            },
        },
        "repository": {
            "name": "ReviewPilot",
            "full_name": "Lohith-004/ReviewPilot",
        },
    }

    body = json.dumps(payload).encode("utf-8")

    mock_job = MagicMock()
    mock_job.id = "duplicate-test-job"

    with patch(
        "app.api.webhooks.review_queue.enqueue",
        return_value=mock_job,
    ) as mock_enqueue, patch(
        "app.api.webhooks.record_webhook_delivery",
        side_effect=[True, False],
    ) as mock_record:

        headers = {
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "duplicate-delivery-123",
            "X-Hub-Signature-256": create_signature(body),
        }

        first_response = client.post(
            "/api/v1/webhooks/github",
            content=body,
            headers=headers,
        )

        second_response = client.post(
            "/api/v1/webhooks/github",
            content=body,
            headers=headers,
        )

    assert first_response.status_code == 202
    assert first_response.json()["status"] == "accepted"

    assert second_response.status_code == 202
    assert second_response.json()["status"] == "duplicate"

    assert mock_record.call_count == 2

    mock_record.assert_any_call(
        delivery_id="duplicate-delivery-123",
        event="pull_request",
        repository="Lohith-004/ReviewPilot",
    )

    mock_enqueue.assert_called_once_with(
        "app.workers.review_worker.process_review_job",
        installation_id=167303229,
        owner="Lohith-004",
        repo="ReviewPilot",
        pull_request_number=42,
    )


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


def test_github_webhook_invalid_json():
    body = b'{"action":"opened",'

    response = client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "invalid-json-123",
            "X-Hub-Signature-256": create_signature(body),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid JSON payload"


def test_github_webhook_payload_too_large():
    body = b"x" * (settings.github_webhook_max_body_bytes + 1)

    response = client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "large-payload-123",
            "X-Hub-Signature-256": create_signature(body),
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "Webhook payload too large"