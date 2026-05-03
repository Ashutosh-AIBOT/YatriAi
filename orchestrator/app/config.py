from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    kafka_bootstrap_servers: str
    kafka_api_key: str = ""
    kafka_api_secret: str = ""
    groq_api_key: str
    google_maps_api_key: str
    amadeus_client_id: str
    amadeus_client_secret: str
    rapidapi_key: str
    zomato_api_key: str
    ola_api_key: str
    uber_server_token: str
    jwt_secret: str
    gateway_base_url: str = "http://localhost:8080"

    class Config:
        env_file = "../.env"
        case_sensitive = False

settings = Settings()
