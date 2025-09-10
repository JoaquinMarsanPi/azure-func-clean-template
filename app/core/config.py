# app/core/config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(".env", raise_error_if_not_found=False))

@dataclass
class Settings:
    # Entorno
    ENV: str = os.getenv("ENV", "dev")

    AZURE_OPENAI_API_KEY: str | None = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_ENGINE: str | None = os.getenv("AZURE_OPENAI_ENGINE")

    COSMOS_URL: str | None = os.getenv("COSMOS_URL")
    COSMOS_KEY: str | None = os.getenv("COSMOS_KEY")
    COSMOS_DB: str = os.getenv("COSMOS_DB", "aiagents")
    KEYVAULT_URI: str | None = os.getenv("KEYVAULT_URI")

settings = Settings()
