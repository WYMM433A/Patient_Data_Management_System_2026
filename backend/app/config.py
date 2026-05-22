from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DEBUG: bool = True
    
    # AI / Gemini
    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""

    # Add these two fields to handle the production environment variables
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    CORS_ORIGINS: str = "[]"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"  # This is the "safety net" to prevent future crashes
    }

settings = Settings()
