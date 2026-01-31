from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "AdaptiveCare System"
    debug: bool = True
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    redis_url: Optional[str] = None
    database_url: Optional[str] = None
    
    simulation_speed: float = 1.0
    simulation_tick_interval: float = 1.0
    
    llm_provider: str = "claude"
    llm_api_key: Optional[str] = None
    llm_model: str = "claude-3-sonnet-20240229"
    
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
