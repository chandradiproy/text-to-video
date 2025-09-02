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

    # Twilio Configuration
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER")


    class Config:
        # This allows the settings to be loaded from a .env file
        case_sensitive = True

# Create a single instance of the settings to be used throughout the application
settings = Settings()

# --- DEBUGGING HELPER ---
if settings.HUGGING_FACE_API_KEY:
    print(f"DEBUG: Loaded Hugging Face Key.")
else:
    print("DEBUG: HUGGING_FACE_API_KEY not found in environment variables.")

if settings.TWILIO_ACCOUNT_SID:
    print(f"DEBUG: Loaded Twilio Account SID.")
else:
    print("DEBUG: TWILIO_ACCOUNT_SID not found in environment variables.")
