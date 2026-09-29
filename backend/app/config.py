from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./memorysupport.db"
    jwt_secret: str = "change-this-secret"
    access_token_expire_minutes: int = 720

    hindsight_api_url: str = "http://localhost:8888"
    hindsight_api_key: str | None = None

    ai_api_url: str | None = None
    ai_api_key: str | None = None
    ai_model: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
