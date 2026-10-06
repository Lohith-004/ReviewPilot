import asyncio
import time

from google import genai
from google.genai.errors import APIError

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
    MAX_RETRIES = 3
    INITIAL_BACKOFF_SECONDS = 2

    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.gemini_api_key)

    async def review(self, filename: str, patch: str) -> ReviewResult:
        start_time = time.perf_counter()

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            "Review this GitHub pull request diff carefully.\n\n"
            f"File:\n{filename}\n\n"
            f"Diff:\n{patch}\n\n"
            "Return only the structured review result."
        )

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                print(
                    f"[LLM] Starting review: {filename} "
                    f"(attempt {attempt}/{self.MAX_RETRIES})"
                )

                interaction = await asyncio.wait_for(
                    self.client.aio.interactions.create(
                        model=settings.gemini_model,
                        input=prompt,
                        response_format={
                            "type": "text",
                            "mime_type": "application/json",
                            "schema": ReviewResult.model_json_schema(),
                        },
                    ),
                    timeout=settings.gemini_timeout_seconds,
                )

                elapsed = time.perf_counter() - start_time

                print(
                    f"[LLM] Completed review: {filename} "
                    f"in {elapsed:.2f}s"
                )

                return ReviewResult.model_validate_json(
                    interaction.output_text
                )

            except asyncio.TimeoutError:
                elapsed = time.perf_counter() - start_time

                if attempt == self.MAX_RETRIES:
                    print(
                        f"[LLM] Gemini timed out after "
                        f"{settings.gemini_timeout_seconds}s "
                        f"on {self.MAX_RETRIES} attempts: {filename}"
                    )
                    raise

                backoff = self.INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))

                print(
                    f"[LLM] Gemini request timed out after "
                    f"{settings.gemini_timeout_seconds}s "
                    f"(elapsed {elapsed:.2f}s). "
                    f"Retrying in {backoff}s..."
                )

                await asyncio.sleep(backoff)

            except APIError as exc:
                status_code = getattr(exc, "code", None)

                if status_code not in {429, 500, 502, 503, 504}:
                    raise

                if attempt == self.MAX_RETRIES:
                    print(
                        f"[LLM] Gemini failed after {self.MAX_RETRIES} "
                        f"attempts: {filename}"
                    )
                    raise

                backoff = self.INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))

                print(
                    f"[LLM] Gemini temporarily unavailable "
                    f"(HTTP {status_code}). "
                    f"Retrying in {backoff}s..."
                )

                await asyncio.sleep(backoff)

        raise RuntimeError("LLM review failed unexpectedly.")