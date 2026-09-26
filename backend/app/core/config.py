from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "Lex-DSS"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_SERVER: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_DB: str = Field(default="lex_dss")
    
    DATABASE_URL: Optional[str] = None
    
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    # --- LLM Provider (OpenAI-compatible) ---
    # Contoh konfigurasi Bazaarlink pada backend/.env:
    #   LLM_PROVIDER=bazaarlink
    #   OPENAI_API_BASE=https://api.bazaarlink.ai/v1
    #   OPENAI_API_KEY=sk-bl-...
    # Penamaan key mengikuti konvensi langchain-openai (OPENAI_BASE_URL / OPENAI_API_KEY).
    LLM_PROVIDER: str = "bazaarlink"
    OPENAI_API_BASE: str = "https://api.bazaarlink.ai/v1"
    OPENAI_API_KEY: Optional[str] = None

    # Model LLM aktif. Fallback gratis (tanpa saldo) yang tersedia di Bazaarlink:
    #   auto:free, deepseek-v4-flash-0731free, qwen/qwen3.7-flash:free
    # Model produksi berbayar (memerlukan saldo): claude-sonnet-4.6, claude-opus-5,
    #   gpt-5.4, gpt-5.6-sol-pro, gemini-3.1-pro-preview, qwen3.8-max, grok-4.7
    LLM_MODEL: str = "auto:free"
    LLM_MODEL_FALLBACKS: list[str] = [
        "deepseek-v4-flash-0731free",
        "qwen/qwen3.7-flash:free",
    ]
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT_SECONDS: int = 120

    # Embedding. Endpoint /v1/embeddings pada Bazaarlink hanya tersedia untuk model
    # berbayar (text-embedding-3-small / -large) dan mengembalikan 402 bila saldo 0.
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    EMBEDDING_PROVIDER: str = "openai"

    REDIS_URL: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()