import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Membase configuration
    membase_id: str = os.getenv("MEMBASE_ID", "fastapi-agent")
    membase_account: str = os.getenv("MEMBASE_ACCOUNT", "")
    membase_secret_key: str = os.getenv("MEMBASE_SECRET_KEY", "")
    membase_hub: str = os.getenv("MEMBASE_HUB", "https://testnet.storage.unibase.site")
    
    # API configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    api_key: Optional[str] = os.getenv("API_KEY", None)
    
    # ChromaDB configuration
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Application metadata
    app_name: str = "Membase API"
    app_version: str = "1.0.0"
    app_description: str = "FastAPI wrapper for Membase SDK - Decentralized AI Memory Layer"
    
    # AIP Configuration
    enable_aip: bool = os.getenv("ENABLE_AIP", "true").lower() == "true"
    aip_grpc_host: str = os.getenv("AIP_GRPC_HOST", "54.169.29.193:8081")
    aip_agent_timeout: int = int(os.getenv("AIP_AGENT_TIMEOUT", "120"))
    aip_max_agents: int = int(os.getenv("AIP_MAX_AGENTS", "10"))
    aip_default_llm: str = os.getenv("AIP_DEFAULT_LLM", "openai")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


# Set environment variables for membase SDK
os.environ["MEMBASE_ID"] = settings.membase_id
os.environ["MEMBASE_ACCOUNT"] = settings.membase_account
os.environ["MEMBASE_SECRET_KEY"] = settings.membase_secret_key
os.environ["MEMBASE_HUB"] = settings.membase_hub