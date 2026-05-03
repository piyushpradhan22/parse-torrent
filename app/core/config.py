"""Configuration settings for the application."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""
    
    # API Keys
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_API_BASE_URL: str = os.getenv("NVIDIA_API_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_API_MODEL: str = os.getenv("NVIDIA_API_MODEL", "meta/llama-3.1-70b-instruct")
    _fallback_models_raw: str = os.getenv(
        "NVIDIA_API_FALLBACK_MODELS",
        "meta/llama-3.1-8b-instruct,meta/llama-2-70b-chat",
    )
    NVIDIA_API_FALLBACK_MODELS = [
        m.strip() for m in _fallback_models_raw.split(",") if m.strip()
    ]
    
    # Application
    APP_NAME: str = "Torrent IMDB Parser"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "torrent_parser")
    
    # IMDB Data
    IMDB_DATASETS_PATH: str = os.getenv("IMDB_DATASETS_PATH", "./data/imdb")
    IMDB_INDEX_PATH: str = os.getenv("IMDB_INDEX_PATH", "./indexer/imdb_index")
    
    # API Settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "7860"))  # HuggingFace default port
    
    # Model Settings
    MODEL_NAME: str = os.getenv("MODEL_NAME", "bert-base-uncased")
    DEVICE: str = os.getenv("DEVICE", "cpu")
    MAX_SEQ_LENGTH: int = 512
    
    # Indexer Settings
    USE_FUZZY_MATCHING: bool = True
    FUZZY_THRESHOLD: float = 0.8


settings = Settings()
