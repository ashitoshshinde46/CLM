from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "GCC Lightweight CLM API"
    api_prefix: str = "/api"
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7
    database_url: str = "postgresql+psycopg2://clm:clm@localhost:5432/clm"


settings = Settings()
