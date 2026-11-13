from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "Millet Milk Sales AI"

    APP_VERSION: str = "1.0.0"

    BUSINESS_NAME: str = "Millet Milk Sales"

    CURRENCY: str = "INR"

    DELIVERY_MODES: str = "home_delivery,pickup"

    PAYMENT_MODES: str = "cash_on_delivery,upi"

    ENVIRONMENT: str = "development"

    API_PREFIX: str = "/api/v1"

    WHATSAPP_ACCESS_TOKEN: str = ""

    WHATSAPP_PHONE_NUMBER_ID: str = ""

    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""

    WHATSAPP_APP_SECRET: str = ""

    WHATSAPP_VERIFY_TOKEN: str = ""

    WHATSAPP_API_VERSION: str = ""

    DATABASE_URL: str = "sqlite:///./millet_milk.db"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TIMEOUT: int = 60

    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma_db"

    CHROMA_COLLECTION_NAME: str = "millet_milk_knowledge"

    RAG_TOP_K: int = 3

    RAG_MAX_COSINE_DISTANCE: float = 0.45

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    LLM_DEFAULT_PROVIDER: str = "ollama"

    CLOUD_LLM_ENABLED: bool = False
    CLOUD_LLM_BASE_URL: str = ""
    CLOUD_LLM_API_KEY: str = ""
    CLOUD_LLM_MODEL: str = ""

    LLM_MAX_RETRIES: int = 1
    LLM_RETRY_DELAY: float = 1.0
    LLM_ENABLE_FALLBACK: bool = True

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300
    REDIS_SESSION_TTL: int = 1800
    REDIS_ENABLED: bool = True

    JWT_SECRET_KEY: str = "millet_milk_dev_jwt_secret_key_2026_change_me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ADMIN_SIGNUP_KEY: str = ""
    TRACKING_WEBHOOK_SECRET: str = ""

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# WHATSAPP_ACCESS_TOKEN: str = ""

# WHATSAPP_PHONE_NUMBER_ID: str = ""

# WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""

# WHATSAPP_APP_SECRET: str = ""

# WHATSAPP_VERIFY_TOKEN: str = ""

# WHATSAPP_API_VERSION: str = ""
