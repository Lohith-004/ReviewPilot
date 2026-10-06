from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    github_app_id: int
    github_client_id: str
    github_private_key_path: str
    github_webhook_secret: str
    github_webhook_max_body_bytes: int = 1_000_000

    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout_seconds: float = 120.0

    redis_url: str = "redis://localhost:6379/0"

    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_base_url: str = "https://cloud.langfuse.com"
    langfuse_tracing_environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()