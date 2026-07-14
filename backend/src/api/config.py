from pydantic_settings import BaseSettings, SettingsConfigDict

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
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Instantiate settings so it can be imported across the app
settings = Settings()
