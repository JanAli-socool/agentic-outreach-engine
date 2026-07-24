"""Central configuration. All env driven, no hardcoded values."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str
    tavily_api_key: str

    cheap_model: str = "llama-3.1-8b-instant"
    strong_model: str = "llama-3.3-70b-versatile"

    max_verifier_retries: int = 2
    confidence_threshold: float = 0.70
    scrape_timeout_seconds: int = 10
    scrape_max_chars: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()