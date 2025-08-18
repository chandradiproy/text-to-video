# backend/app/core/config.py

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Configuration settings for the application, loaded from environment variables.
    """
    # Hugging Face API Key.
    HUGGING_FACE_API_KEY: str = os.getenv("HUGGING_FACE_API_KEY")

    class Config:
        # This allows the settings to be loaded from a .env file
        case_sensitive = True

# Create a single instance of the settings to be used throughout the application
settings = Settings()

# --- DEBUGGING HELPER ---
if settings.HUGGING_FACE_API_KEY:
    token = settings.HUGGING_FACE_API_KEY
    print(f"DEBUG: Loaded Hugging Face Key starts with: {token[:5]}...")
else:
    print("DEBUG: HUGGING_FACE_API_KEY not found in environment variables.")
