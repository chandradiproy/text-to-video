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
    # Hugging Face API Key
    HUGGING_FACE_API_KEY: str = os.getenv("HUGGING_FACE_API_KEY")

    # Twilio Credentials
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER")

    # --- NEW: MongoDB Atlas Connection String ---
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    

    class Config:
        case_sensitive = True

# Create a single instance of the settings to be used throughout the application
settings = Settings()

# --- DEBUGGING HELPER ---
if not all([settings.HUGGING_FACE_API_KEY, settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_WHATSAPP_NUMBER, settings.MONGODB_URI]):
    print("DEBUG: One or more required environment variables are missing.")
else:
    print("DEBUG: All required environment variables are loaded.")

