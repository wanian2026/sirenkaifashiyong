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

    # 安全配置
    ENCRYPTION_KEY: str = "your-encryption-key-change-in-production-use-fernet-key"  # 用于API密钥加密
    ENCRYPTION_KEY_LENGTH: int = 44  # Fernet密钥长度
    AUDIT_LOG_ENABLED: bool = True  # 是否启用审计日志
    AUDIT_LOG_RETENTION_DAYS: int = 90  # 审计日志保留天数
    SENSITIVE_OPERATIONS_VERIFY: bool = True  # 是否启用敏感操作二次验证
    SENSITIVE_OPERATIONS: list = [
        "bot:delete",
        "user:delete",
        "system:configure",
        "api_key:update"
    ]  # 敏感操作列表
    MAX_LOGIN_ATTEMPTS: int = 5  # 最大登录尝试次数
    LOGIN_LOCKOUT_DURATION: int = 1800  # 登录锁定时长（秒），30分钟

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
