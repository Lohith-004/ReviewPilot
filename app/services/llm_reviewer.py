from google import genai

from app.core.config import settings
from app.schemas.review import ReviewResult


SYSTEM_PROMPT = (
    "You are ReviewPilot, an expert AI code reviewer.\n\n"
    "Review the provided GitHub pull request diff carefully.\n\n"
    "Identify only genuine and actionable issues.\n\n"
    "Focus on:\n"
    "1. Bugs\n"
    "2. Security vulnerabilities\n"
    "3. Performance problems\n"
    "4. Important code-quality issues\n\n"
    "Do NOT report:\n"
    "- Personal style preferences\n"
    "- Minor formatting issues\n"
    "- Issues not clearly supported by the diff\n"
    "- Hypothetical problems without reasonable evidence\n"
    "- Duplicate findings\n\n"
    "For every finding:\n"
    "- Identify the exact file.\n"
    "- Identify the relevant line number.\n"
    "- Assign an appropriate severity.\n"
    "- Assign a category.\n"
    "- Explain the problem clearly.\n"
    "- Provide a practical suggested fix.\n\n"
    "If there are no genuine issues, return an empty findings list.\n\n"
    "Be conservative. False positives are worse than missing a minor issue."
)


class LLMReviewer:
    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    async def review(
        self,
        filename: str,
        patch: str,
    ) -> ReviewResult:
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            "Review this GitHub pull request diff.\n\n"
            f"File:\n{filename}\n\n"
            f"Diff:\n{patch}\n\n"
            "Return only the structured review result."
        )

        interaction = await self.client.aio.interactions.create(
            model=settings.gemini_model,
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": ReviewResult.model_json_schema(),
            },
        )

        return ReviewResult.model_validate_json(
            interaction.output_text
        )