"""Configuration settings for the application."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""

    # Only secret — must be provided via environment variable.
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")

    # NVIDIA API — hard-coded defaults.
    NVIDIA_API_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_API_MODEL: str = "meta/llama-3.1-70b-instruct"
    NVIDIA_API_FALLBACK_MODELS: list = [
        "meta/llama-3.1-8b-instruct",
        "meta/llama-2-70b-chat",
    ]

    # Application
    APP_NAME: str = "Torrent IMDB Parser"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # IMDB Data paths
    IMDB_DATASETS_PATH: str = "./data/imdb"
    IMDB_INDEX_PATH: str = "./indexer/imdb_index"

    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 7860

    # Indexer
    USE_FUZZY_MATCHING: bool = True
    FUZZY_THRESHOLD: float = 0.8


settings = Settings()
