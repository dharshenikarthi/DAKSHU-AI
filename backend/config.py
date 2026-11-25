import os
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root or backend dir
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Settings:
    # Project Info
    PROJECT_NAME: str = "DAKSHU AI"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

    # Security & Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dakshu-super-secret-production-key-change-in-prod-884849302")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")) # 7 days
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000,http://127.0.0.1:5500").split(",")
        if origin.strip()
    ]

    # Database
    db_default = "/tmp/dakshu.db" if os.getenv("VERCEL") else "./dakshu.db"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{db_default}")

    # AI Model Configuration
    # Options: "ollama", "transformers", "builtin", "groq", "gemini", "openai_compatible"
    AI_BACKEND: str = os.getenv("AI_BACKEND", "ollama")
    
    # Gemma Ollama Config (Local fine-tuned Dakshu model)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "dakshu")
    OLLAMA_FALLBACK_MODEL: str = os.getenv("OLLAMA_FALLBACK_MODEL", "gemma2:2b")

    # Local Transformers / PyTorch Model Settings (In-Memory Inference)
    LOCAL_MODEL_PATH: str = os.getenv("LOCAL_MODEL_PATH", "./model/dakshu-merged")
    HF_MODEL_ID: str = os.getenv("HF_MODEL_ID", "google/gemma-2-2b-it")

    # Groq Hosted Inference (Ultra-fast LLM API)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

    # Google Gemini API Config
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # Hugging Face Config
    HF_API_KEY: str = os.getenv("HF_API_KEY", "")
    HF_MODEL_ID: str = os.getenv("HF_MODEL_ID", "google/gemma-2-2b-it")

    # OpenAI-Compatible Endpoint Config (vLLM / Groq / OpenRouter / etc.)
    OPENAI_COMPATIBLE_BASE_URL: str = os.getenv("OPENAI_COMPATIBLE_BASE_URL", "")
    OPENAI_COMPATIBLE_API_KEY: str = os.getenv("OPENAI_COMPATIBLE_API_KEY", "")
    OPENAI_COMPATIBLE_MODEL: str = os.getenv("OPENAI_COMPATIBLE_MODEL", "gemma-2-9b-it")

    # Chat & Context Limits
    MAX_HISTORY_TURNS: int = int(os.getenv("MAX_HISTORY_TURNS", "10"))
    MAX_TOKENS_OUTPUT: int = int(os.getenv("MAX_TOKENS_OUTPUT", "1024"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))

settings = Settings()

