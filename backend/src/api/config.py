from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr

class Settings(BaseSettings):
    """
    Application settings managed by pydantic-settings.
    This reads from environment variables and validates them.
    """
    app_env: str = "development"
    port: int = 8000
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_saas"
    supabase_url: str = "https://your-project.supabase.co"
    supabase_jwt_secret: str = "your-jwt-secret-here"
    supabase_key: str = "your-supabase-service-role-key"
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini/gemini-2.0-flash"
    conversation_window_messages: int = Field(default=8, ge=0, le=50)
    conversation_history_max_characters: int = Field(default=6_000, ge=0, le=24_000)
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Instantiate settings so it can be imported across the app
settings = Settings()
