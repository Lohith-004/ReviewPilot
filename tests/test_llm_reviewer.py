from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.review import (
    FindingCategory,
    FindingSeverity,
    ReviewResult,
)
from app.services.llm_reviewer import LLMReviewer


@pytest.mark.asyncio
async def test_llm_reviewer_returns_structured_result():
    expected_result = ReviewResult(
        findings=[
            {
                "file": "app/main.py",
                "line": 10,
                "severity": FindingSeverity.HIGH,
                "category": FindingCategory.BUG,
                "explanation": "Variable may be used before initialization.",
                "suggested_fix": "Initialize the variable before using it.",
            }
        ]
    )

    mock_interaction = MagicMock()
    mock_interaction.output_text = expected_result.model_dump_json()

    mock_interactions = MagicMock()
    mock_interactions.create = AsyncMock(
        return_value=mock_interaction
    )

    mock_client = MagicMock()
    mock_client.aio.interactions = mock_interactions

    with patch(
        "app.services.llm_reviewer.genai.Client",
        return_value=mock_client,
    ):
        reviewer = LLMReviewer()

        result = await reviewer.review(
            filename="app/main.py",
            patch="""@@ -8,3 +8,4 @@
 def example():
+    print(undefined_variable)
""",
        )

    assert isinstance(result, ReviewResult)
    assert len(result.findings) == 1
    assert result.findings[0].file == "app/main.py"
    assert result.findings[0].severity == FindingSeverity.HIGH

    mock_interactions.create.assert_awaited_once()