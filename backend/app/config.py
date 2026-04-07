from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/govfinder"

    # Auth
    SECRET_KEY: str = "changeme"
    KAKAO_CLIENT_ID: str = ""
    KAKAO_CLIENT_SECRET: str = ""

    # External APIs
    DATA_GO_KR_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    RESEND_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # AI
    AI_DAILY_SUMMARY_LIMIT: int = 100

    # Admin
    ADMIN_EMAILS: str = ""  # comma-separated

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"  # comma-separated

    # Environment
    ENV: str = "development"  # development | production

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"


settings = Settings()
