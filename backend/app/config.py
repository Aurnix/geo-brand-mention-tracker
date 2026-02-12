from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    PERPLEXITY_API_KEY: str = ""
    GOOGLE_AI_API_KEY: str = ""

    PARSER_MODEL: str = "gpt-4o-mini"
    PARSER_PROVIDER: str = "openai"

    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    RUN_SCHEDULE_HOUR: int = 3
    RUN_SCHEDULE_MINUTE: int = 0


@lru_cache
def get_settings() -> Settings:
    return Settings()
