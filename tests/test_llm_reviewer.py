import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from google.genai.errors import APIError

from app.schemas.review import ReviewResult
from app.services.llm_reviewer import LLMReviewer
from app.core.config import settings


def create_mock_interaction():
    interaction = MagicMock()
    interaction.output_text = '{"findings": []}'
    return interaction


@pytest.mark.asyncio
async def test_llm_reviewer_success():
    reviewer = LLMReviewer()

    mock_interaction = create_mock_interaction()

    with patch(
        "app.services.llm_reviewer.get_langfuse_client",
        return_value=None,
    ), patch.object(
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

    with patch(
        "app.services.llm_reviewer.get_langfuse_client",
        return_value=None,
    ), patch.object(
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

    with patch(
        "app.services.llm_reviewer.get_langfuse_client",
        return_value=None,
    ), patch.object(
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

    with patch(
        "app.services.llm_reviewer.get_langfuse_client",
        return_value=None,
    ), patch.object(
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


@pytest.mark.asyncio
async def test_llm_reviewer_creates_langfuse_generation():
    reviewer = LLMReviewer()

    mock_interaction = create_mock_interaction()

    mock_langfuse = MagicMock()
    mock_generation = MagicMock()

    mock_langfuse.start_as_current_observation.return_value.__enter__.return_value = (
        mock_generation
    )

    with patch(
        "app.services.llm_reviewer.get_langfuse_client",
        return_value=mock_langfuse,
    ), patch.object(
        reviewer.client.aio.interactions,
        "create",
        new_callable=AsyncMock,
        return_value=mock_interaction,
    ):

        result = await reviewer.review(
            filename="app/main.py",
            patch="+print('secret SQL query')",
        )

    assert isinstance(result, ReviewResult)

    mock_langfuse.start_as_current_observation.assert_called_once_with(
        name="gemini-code-review",
        as_type="generation",
        model=settings.gemini_model,
        metadata={
            "filename": "app/main.py",
        },
    )

    mock_generation.update.assert_called()

    mock_langfuse.flush.assert_called_once()


@pytest.mark.asyncio
async def test_llm_reviewer_does_not_store_raw_patch_in_langfuse():
    reviewer = LLMReviewer()

    mock_interaction = create_mock_interaction()

    mock_langfuse = MagicMock()
    mock_generation = MagicMock()

    mock_langfuse.start_as_current_observation.return_value.__enter__.return_value = (
        mock_generation
    )

    sensitive_patch = "SELECT * FROM users WHERE password = 'super-secret-value'"

    with patch(
        "app.services.llm_reviewer.get_langfuse_client",
        return_value=mock_langfuse,
    ), patch.object(
        reviewer.client.aio.interactions,
        "create",
        new_callable=AsyncMock,
        return_value=mock_interaction,
    ):

        await reviewer.review(
            filename="app/auth.py",
            patch=sensitive_patch,
        )

    observation_call = (
        mock_langfuse.start_as_current_observation.call_args
    )

    observation_arguments = str(observation_call)

    assert sensitive_patch not in observation_arguments

    for call in mock_generation.update.call_args_list:
        assert sensitive_patch not in str(call)