from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model_primary: str = "llama3-70b-8192"
    groq_model_fallback: str = "mixtral-8x7b-32768"
    max_claims: int = 10
    search_results_per_claim: int = 4
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    request_timeout: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
