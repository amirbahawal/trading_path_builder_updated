from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields from .env (e.g., PAYMENT_MODE that was removed)
    )
    
    # Environment
    ENV: str = "development"
    DATA_DIR: str = "./data"
    
    # Database
    DATABASE_URL: str = "sqlite:///./dev.db"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_OUTPUT_TOKENS: int = 2000
    
    # Payment (disabled - instant unlock only)
    # Note: $5 is displayed but not charged - single click unlocks all stages
    PRICE_USD: float = 5.0  # Display price only (not actually charged)
    
    # Paywall
    PAYWALL_ENABLED: str = "true"
    FREE_STAGE_ID: int = 1
    TEMPLATE_VERSION: str = "1.0"
    ALLOW_ANON_PLAN: str = "true"
    
    # Authentication
    JWT_SECRET: str = "dev_secret_change_in_production"
    APP_AUTH_SECRET: str = "dev-secret-change-me"  # For magic link tokens
    EMAIL_SERVICE_API_KEY: str = ""
    
    # Email/Gmail
    GMAIL_ADDRESS: str = ""
    GMAIL_APP_PASSWORD: str = ""
    
    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_HOST: str = "http://127.0.0.1:8000"
    ALLOWED_ORIGINS: str = ""  # Comma-separated list of additional allowed origins
    
    # Logging
    LOG_DIR: str = "./logs"  # Directory for log files
    
    @property
    def PLANS_FILE(self) -> str:
        return f"{self.DATA_DIR}/plans.json"
    
    @property
    def USERS_FILE(self) -> str:
        return f"{self.DATA_DIR}/users.json"
    
    @property
    def MOCK_PLANS_FILE(self) -> str:
        return f"{self.DATA_DIR}/mock_plans.json"
    
    @property
    def QUIZ_FILE(self) -> str:
        return f"{self.DATA_DIR}/quiz_questions.json"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()