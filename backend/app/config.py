from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://jobagent:jobagent_secret@localhost:5432/jobagent"
    REDIS_URL: str = "redis://localhost:6379/0"
    OPENAI_API_KEY: str = ""
    ENCRYPTION_KEY: str = ""
    SECRET_KEY: str = ""
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Job Search Config
    MAX_DAILY_APPLICATIONS: int = 20
    RATE_LIMIT_DELAY_MIN: float = 30.0
    RATE_LIMIT_DELAY_MAX: float = 120.0
    MATCH_SCORE_THRESHOLD: float = 0.75

    # Playwright
    HEADLESS: bool = True
    BROWSER_PROFILE_DIR: str = "./browser_profiles"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
