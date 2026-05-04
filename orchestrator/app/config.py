from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # === LLM Key (will fail at LLM call time if not set, but server starts) ===
    groq_api_key: str = ""
    jwt_secret: str = "yatri_ai_default_dev_secret_key_32chars"

    # === Database (defaults for Docker/HF monolith) ===
    database_url: str = "postgresql+asyncpg://yatri:yatri@localhost:5432/yatri_db"
    redis_url: str = "redis://localhost:6379"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_api_key: str = ""
    kafka_api_secret: str = ""

    # === Optional Travel API Keys (graceful fallback if missing) ===
    google_maps_api_key: str = ""
    amadeus_client_id: str = ""
    amadeus_client_secret: str = ""
    rapidapi_key: str = ""
    zomato_api_key: str = ""
    ola_api_key: str = ""
    uber_server_token: str = ""

    # === App Config ===
    gateway_base_url: str = "http://localhost:8080"
    cors_allowed_origins: str = "http://localhost:3000"

    class Config:
        env_file = "../.env"
        case_sensitive = False
        extra = "ignore"

    def is_api_available(self, key_name: str) -> bool:
        """Check if a specific API key is configured (not a placeholder)."""
        val = getattr(self, key_name, "")
        return bool(val) and val not in ("", "your_key", "your_token", "your_secret", "your_id", "your_maps_key")

settings = Settings()

# Log which APIs are available at startup
_apis = ["google_maps_api_key", "amadeus_client_id", "rapidapi_key", "zomato_api_key", "ola_api_key", "uber_server_token"]
for _api in _apis:
    if settings.is_api_available(_api):
        logger.info(f"✅ {_api} is configured")
    else:
        logger.warning(f"⚠️  {_api} is NOT configured — agent will use fallback data")
