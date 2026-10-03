import hashlib
import hmac

from app.services.github_webhook import verify_github_signature


def test_valid_github_signature():
    secret = "test-secret"
    payload = b'{"action":"opened"}'

    digest = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    signature = f"sha256={digest}"

    assert verify_github_signature(
        payload,
        signature,
        secret,
    )


def test_invalid_github_signature():
    secret = "test-secret"
    payload = b'{"action":"opened"}'

    signature = "sha256=invalid"

    assert not verify_github_signature(
        payload,
        signature,
        secret,
    )


def test_missing_github_signature():
    secret = "test-secret"
    payload = b'{"action":"opened"}'

    assert not verify_github_signature(
        payload,
        None,
        secret,
    )