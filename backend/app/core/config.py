from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
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
    CORS_ORIGIN: str = "http://localhost:5173"
    
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    # --- LLM Configuration (sama dengan lex-integrity) ---
    # Ollama (Local LLM)
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="deepseek-r1:8b")  # dari Modelfile lex-integrity
    OLLAMA_EMBED_MODEL: str = Field(default="nomic-embed-text")  # embedding model
    OLLAMA_AGENT_MODEL: str = Field(default="lex-integrity-agent:latest")  # custom model
    OLLAMA_TEMPERATURE: float = Field(default=0.2)  # dari Modelfile
    OLLAMA_TOP_P: float = Field(default=0.9)
    OLLAMA_NUM_CTX: int = Field(default=4096)
    MAX_HOPS: int = Field(default=4)
    MAX_SUB_QUERIES: int = Field(default=3)
    
    # Gemini API (Fallback cloud)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash")
    GEMINI_MAX_OUTPUT_TOKENS: int = Field(default=4096)
    
    # Bazaarlink / OpenAI-compatible (Alternative)
    LLM_PROVIDER: str = Field(default="ollama")  # ollama, gemini, bazaarlink
    OPENAI_API_BASE: str = Field(default="https://api.bazaarlink.ai/v1")
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = Field(default="auto:free")
    LLM_MODEL_FALLBACKS: List[str] = Field(default=[
        "deepseek-v4-flash-0731free",
        "qwen/qwen3.7-flash:free",
    ])
    LLM_TEMPERATURE: float = Field(default=0.1)
    LLM_MAX_TOKENS: int = Field(default=4096)
    LLM_TIMEOUT_SECONDS: int = Field(default=120)
    
    # Embedding
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-small")  # fallback
    EMBEDDING_DIMENSION: int = Field(default=1536)
    EMBEDDING_PROVIDER: str = Field(default="ollama")  # ollama, openai
    
    REDIS_URL: str = "redis://localhost:6379/0"
    LEX_INTEGRITY_URL: str = "http://localhost:3000"
    INTERNAL_API_KEY: Optional[str] = None

    # E-Netizen civic polling. Mirrors LEX_DSS_HMAC_SECRET on the e-voting side.
    ENETIZEN_URL: str = "http://localhost:8000"
    ENETIZEN_HMAC_SECRET: Optional[str] = None

    # External public-sector data integrations. Secrets stay in .env only.
    SIPP_API_BASE_URL: Optional[str] = None
    SIPP_API_KEY: Optional[str] = None
    JDIHN_API_BASE_URL: Optional[str] = None
    JDIHN_API_KEY: Optional[str] = None
    OSS_API_BASE_URL: Optional[str] = None
    OSS_API_CLIENT_ID: Optional[str] = None
    OSS_API_CLIENT_SECRET: Optional[str] = None
    DJP_API_BASE_URL: Optional[str] = None
    DJP_API_CLIENT_ID: Optional[str] = None
    DJP_API_CLIENT_SECRET: Optional[str] = None
    KEMENPERIN_API_BASE_URL: Optional[str] = None
    KEMENPERIN_API_KEY: Optional[str] = None
    DPR_API_BASE_URL: Optional[str] = None
    DPR_API_KEY: Optional[str] = None
    
    # CAPTCHA Configuration (multi-provider: hcaptcha, math, none)
    # hCaptcha (privacy-focused, drop-in replacement for reCAPTCHA)
    # Dapat diakses di https://hcaptcha.com/
    HCAPTCHA_SECRET_KEY: Optional[str] = None
    HCAPTCHA_SITE_KEY: Optional[str] = None

    # CAPTCHA Provider: "hcaptcha" | "math" | "none"
    CAPTCHA_PROVIDER: str = "none"  # Set "hcaptcha" or "math" di production
    CAPTCHA_ENABLED: bool = False
    CAPTCHA_THRESHOLD: float = 0.5  # Score threshold (hCaptcha)
    
    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1).replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGIN.split(",") if origin.strip()]
    
    # System prompt dari Modelfile lex-integrity
    SYSTEM_PROMPT: str = """Kamu adalah Lex-Integrity AI Agent, seorang pakar integritas hukum, kebijakan publik, dan keadilan sosial Indonesia. Kamu bertindak bukan sekadar sebagai mesin pembaca aturan, melainkan sebagai penegak keadilan yang jujur, adil, berempati, dan memiliki rasa kemanusiaan yang tinggi.

PRINSIP UTAMA & NILAI MORAL:
1. KEJUJURAN TANPA KOMPROMI (Honesty): 
   - Ungkapkan celah hukum, "pasal selundupan", dan potensi abuse of power secara transparan tanpa ditutup-tutupi. Jangan pernah merekayasa atau membuat-buat pasal fiktif.

2. KEADILAN SEJATI (Fairness & Justice):
   - Evaluasi hukum dari asas kepastian dan keadilan publik. Jika aturan turunan (Perda/Perpres) mencederai prinsip dasar hukum di atasnya atau merugikan hak masyarakat luas demi kepentingan segelintir pihak, nyatakan secara tegas.

3. EMPATI & KEMANUSIAAN (Empathy & Compassion):
   - Dalam menganalisis dampak kebijakan, posisikan dirimu dari sudut pandang masyarakat terdampak (masyarakat adat, buruh, warga lokal, kelompok rentan, dan generasi mendatang).
   - Analisis dampak tidak hanya berupa angka/ekonomi, tetapi juga dampak kemanusiaan: ruang hidup, lingkungan, kesejahteraan, dan rasa keadilan sosial.

ATURAN BAHASA, ANALISIS & OUTPUT:
- WAJIB DAN MUTLAK MENGGUNAKAN BAHASA INDONESIA yang baku, komunikatif, dan tegas dalam SELURUH tanggapan dan analisis. DILARANG menggunakan Bahasa Inggris.
- Saat menganalisis pertentangan antar-pasal, selalu pertimbangkan aspek perlindungan Hak Asasi Manusia (HAM) dan kelestarian lingkungan.
- Berikan narasi yang tegas namun tetap santun, beretika, dan memperhitungkan penderitaan/kerugian emosional-sosial masyarakat yang mungkin timbul akibat penyalahgunaan wewenang.
- Jika diminta mengembalikan format JSON, pastikan struktur data tetap valid sambil mempertahankan poin analisis yang berempati dan adil."""


settings = Settings()
