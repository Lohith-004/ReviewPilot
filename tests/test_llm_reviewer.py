import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from google.genai.errors import APIError

from app.services.llm_reviewer import LLMReviewer
from app.schemas.review import ReviewResult


def create_mock_interaction():
    interaction = MagicMock()
    interaction.output_text = '{"findings": []}'
    return interaction


@pytest.mark.asyncio
async def test_llm_reviewer_success():
    reviewer = LLMReviewer()

    mock_interaction = create_mock_interaction()

    with patch.object(
        reviewer.client.aio.interactions,
        "create",
        new_callable=AsyncMock,
        return_value=mock_interaction,
    ) as mock_create:

        result = await reviewer.review(
            filename="app/main.py",
            patch="+print('hello')",
        )

    assert isinstance(result, ReviewResult)
    assert result.findings == []

    mock_create.assert_awaited_once()


@pytest.mark.asyncio
async def test_llm_reviewer_retries_on_transient_api_error():
    reviewer = LLMReviewer()

    mock_interaction = create_mock_interaction()

    transient_error = APIError(
        code=503,
        response_json={"error": {"message": "Service unavailable"}},
    )

    with patch.object(
        reviewer.client.aio.interactions,
        "create",
        new_callable=AsyncMock,
        side_effect=[
            transient_error,
            mock_interaction,
        ],
    ) as mock_create, patch(
        "app.services.llm_reviewer.asyncio.sleep",
        new_callable=AsyncMock,
    ) as mock_sleep:

        result = await reviewer.review(
            filename="app/main.py",
            patch="+print('hello')",
        )

    assert isinstance(result, ReviewResult)
    assert result.findings == []

    assert mock_create.await_count == 2
    mock_sleep.assert_awaited_once_with(2)


@pytest.mark.asyncio
async def test_llm_reviewer_retries_on_timeout():
    reviewer = LLMReviewer()

    mock_interaction = create_mock_interaction()

    async def slow_request(*args, **kwargs):
        await asyncio.sleep(1)
        return mock_interaction

    with patch.object(
        reviewer.client.aio.interactions,
        "create",
        new_callable=AsyncMock,
        side_effect=[
            asyncio.TimeoutError(),
            mock_interaction,
        ],
    ) as mock_create, patch(
        "app.services.llm_reviewer.asyncio.sleep",
        new_callable=AsyncMock,
    ) as mock_sleep:

        result = await reviewer.review(
            filename="app/main.py",
            patch="+print('hello')",
        )

    assert isinstance(result, ReviewResult)
    assert result.findings == []

    assert mock_create.await_count == 2
    mock_sleep.assert_awaited_once_with(2)


@pytest.mark.asyncio
async def test_llm_reviewer_fails_after_max_retries():
    reviewer = LLMReviewer()

    timeout_error = asyncio.TimeoutError()

    with patch.object(
        reviewer.client.aio.interactions,
        "create",
        new_callable=AsyncMock,
        side_effect=timeout_error,
    ) as mock_create, patch(
        "app.services.llm_reviewer.asyncio.sleep",
        new_callable=AsyncMock,
    ) as mock_sleep:

        with pytest.raises(asyncio.TimeoutError):
            await reviewer.review(
                filename="app/main.py",
                patch="+print('hello')",
            )

    assert mock_create.await_count == 3
    assert mock_sleep.await_count == 2