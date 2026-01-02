from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./crypto_bot.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    EXCHANGE_ID: str = "binance"
    API_KEY: str = ""
    API_SECRET: str = ""
    GRID_LEVELS: int = 10
    GRID_SPACING: float = 0.02
    INVESTMENT_AMOUNT: float = 1000
    LOG_LEVEL: str = "INFO"

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_ENABLED: bool = False
    CACHE_TTL_DEFAULT: int = 60  # 默认缓存时间（秒）

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
