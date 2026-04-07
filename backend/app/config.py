from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/govfinder"
    SECRET_KEY: str = "changeme"
    KAKAO_CLIENT_ID: str = ""
    KAKAO_CLIENT_SECRET: str = ""
    DATA_GO_KR_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
