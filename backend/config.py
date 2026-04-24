from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    anthropic_api_key: str
    supabase_url: str
    supabase_key: str
    supabase_db_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days
    ruflo_mcp_url: str = "https://mcpmarket.com/server/ruflo"
    nadac_api_url: str = "https://data.cms.gov/api/1/datastore/query/9778fb52-45c2-4df2-94f0-e3f5b50b8a8d/0"
    claude_model: str = "claude-opus-4-6"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
