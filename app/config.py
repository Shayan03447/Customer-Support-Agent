# Application configuration using pydantic-settings.
#
# To implement:
#   class Settings(BaseSettings):
#     Define all environment variables here with types and defaults.
#     Add fields in the order you need them:
#       Step 1 → openai_api_key, openai_model
#       Step 2 → meta_app_id, meta_app_secret, meta_verify_token
#       Step 3 → database_url
#       Step 4 → redis_url
#       Step 5 → default_crm_base_url, default_crm_api_key
#       Step 6 → slack_webhook_url, alert_email
#       Step 7 → sentry_dsn
#       App    → app_env, log_level
#
#     class Config:
#         env_file = ".env"
#         case_sensitive = False
#
# Export: settings = Settings() singleton using @lru_cache
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    class Config:
        env_file=".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings=get_settings()