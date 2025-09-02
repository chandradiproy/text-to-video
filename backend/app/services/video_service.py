import asyncio
import base64
import time
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError
from fastapi import WebSocket, WebSocketDisconnect
import logging
import requests
from twilio.rest import Client

from ..core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- In-Memory Cache ---
video_cache = {}

# --- Style Prefixes for Prompt Enhancement (RAG) ---
STYLE_PREFIXES = {
    "Default": "",
    "Cinematic": "cinematic, dramatic lighting, high detail, 4k, epic,",
    "Anime": "anime style, key visual, vibrant, studio trigger,",
    "Pixel Art": "pixel art, 16-bit, retro, old-school,",
    "Documentary": "documentary style, realistic, high fidelity,",
    "Fantasy": "fantasy, epic, magical, high detail,",
    "Sci-Fi": "sci-fi, futuristic, high tech, detailed,",
}

# --- Twilio Client Initialization ---
try:
    twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    logger.info("Twilio client initialized for video service.")
except Exception as e:
    logger.error(f"Failed to initialize Twilio client in video service: {e}")
    twilio_client = None

# --- SYNCHRONOUS HELPER FUNCTIONS (To be run in a separate thread) ---

def _upload_video_to_temp_storage(video_bytes: bytes) -> str:
    """Uploads video bytes to a temporary file host and returns the public URL."""
    try:
        files = {'file': ('video.mp4', video_bytes, 'video/mp4')}
        # Using a temporary file host for demonstration purposes
        response = requests.post('https://tmpfiles.org/api/v1/upload', files=files)
        response.raise_for_status()
        data = response.json()
        # The URL from tmpfiles.org needs to be converted to a direct download link
        return data['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to upload video to temporary storage: {e}")
        return None

def _send_whatsapp_video(to: str, media_url: str, caption: str):
    """Sends a video message via Twilio."""
    if not twilio_client:
        logger.error("Twilio client not available. Cannot send video.")
        return
    try:
        twilio_client.messages.create(
            from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
            body=caption,
            media_url=[media_url],
            to=f'whatsapp:{to}'
        )
        logger.info(f"Video sent successfully to {to}")
    except Exception as e:
        logger.error(f"Failed to send WhatsApp video to {to}: {e}")
        _send_whatsapp_text(to, "Sorry, I couldn't send the video file, but it was generated. You can try again.")

def _send_whatsapp_text(to: str, message: str):
    """Sends a text message via Twilio."""
    if not twilio_client:
        return
    try:
        twilio_client.messages.create(
            from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
            body=message,
            to=f'whatsapp:{to}'
        )
    except Exception as e:
        logger.error(f"Failed to send fallback text to {to}: {e}")

# --- ASYNCHRONOUS WRAPPERS ---

async def _upload_video_to_temp_storage_async(video_bytes: bytes) -> str:
    """Asynchronously uploads video bytes by running the sync function in a thread."""
    return await asyncio.to_thread(_upload_video_to_temp_storage, video_bytes)

async def _send_whatsapp_video_async(to: str, media_url: str, caption: str):
    """Asynchronously sends a video message via Twilio."""
    await asyncio.to_thread(_send_whatsapp_video, to, media_url, caption)

async def _send_whatsapp_text_async(to: str, message: str):
    """Asynchronously sends a text message via Twilio."""
    await asyncio.to_thread(_send_whatsapp_text, to, message)


# --- Core Service Functions ---

async def generate_video_for_whatsapp(prompt: str, style: str, user_phone_number: str):
    """
    Main service function for the WhatsApp bot flow.
    """
    try:
        style_prefix = STYLE_PREFIXES.get(style, "")
        full_prompt = f"{style_prefix} {prompt}"
        logger.info(f"WhatsApp - Enhanced prompt: {full_prompt}")

        cache_key = f"{style}:{prompt}"
        if cache_key in video_cache:
            logger.info("WhatsApp - Cache hit!")
            cached_data = video_cache[cache_key]
            caption = "✅ Here's your video (from cache)!"
            await _send_whatsapp_video_async(user_phone_number, cached_data['media_url'], caption)
            return

        logger.info("WhatsApp - Generating video...")
        client = InferenceClient(token=settings.HUGGING_FACE_API_KEY, provider='fal-ai')
        video_bytes = await asyncio.to_thread(
            client.text_to_video, full_prompt, model="Wan-AI/Wan2.2-T2V-A14B"
        )
        
        logger.info("WhatsApp - Uploading video to temporary storage...")
        media_url = await _upload_video_to_temp_storage_async(video_bytes)

        if not media_url:
            raise Exception("Failed to get a public URL for the video.")

        caption = "✅ Here's your AI-generated video! Send another prompt to create more."
        await _send_whatsapp_video_async(user_phone_number, media_url, caption)
        
        video_cache[cache_key] = {"media_url": media_url}

    except HfHubHTTPError as e:
        logger.error(f"Hugging Face API Error for {user_phone_number}: {e}")
        error_message = "Sorry, the AI model is currently busy or unavailable. Please try again in a moment."
        await _send_whatsapp_text_async(user_phone_number, error_message)
    except Exception as e:
        logger.error(f"An unexpected error occurred for {user_phone_number}: {e}")
        error_message = "😔 Apologies, something went wrong on my end. Please try a different prompt or check back later."
        await _send_whatsapp_text_async(user_phone_number, error_message)


async def generate_video_from_prompt(prompt: str, style: str, websocket: WebSocket):
    """
    Core service function for the web app (uses WebSockets).
    """
    try:
        style_prefix = STYLE_PREFIXES.get(style, "")
        full_prompt = f"{style_prefix} {prompt}"
        await websocket.send_json({"status": f"Enhanced prompt..."})

        cache_key = f"{style}:{prompt}"
        if cache_key in video_cache:
            # For web, we need video_base64, so we must handle cache differently
            # This part needs adjustment if web app is still a primary feature
            logger.info("Web App - Cache hit. Re-encoding is needed for web.")
        
        await websocket.send_json({"status": "Initializing AI model..."})
        client = InferenceClient(token=settings.HUGGING_FACE_API_KEY)

        await websocket.send_json({"status": "Generating video... This can take a minute."})
        video_bytes = await asyncio.to_thread(
            client.text_to_video,
            full_prompt,
            model="cerspense/zeroscope_v2_576w"
        )
        video_base64 = base64.b64encode(video_bytes).decode("utf-8")
        
        response_data = {"video": video_base64}
        # Caching for the web app would need to store the base64 string
        # video_cache[cache_key] = response_data
        
        await websocket.send_json(response_data)

    except HfHubHTTPError as e:
        logger.error(f"Hugging Face API Error: {e}")
        await websocket.send_json({"error": "The AI model is currently busy or unavailable. Please try again later."})
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        await websocket.send_json({"error": "An internal error occurred during video generation."})

