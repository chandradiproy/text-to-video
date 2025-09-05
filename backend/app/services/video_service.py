# backend/app/services/video_service.py

import asyncio
import base64
import logging
import os
import tempfile
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from moviepy import VideoFileClip
import requests
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError
from fastapi import WebSocket

from ..core.config import settings
from ..db.database import save_generation_history, clear_user_state
from . import llm_service 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- In-memory cache for WebSocket results ---
video_cache = {}

# --- Twilio Client Initialization ---
try:
    twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    logger.info("Twilio client initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Twilio client: {e}")
    twilio_client = None

# --- Synchronous Helper Functions ---

def _upload_video_to_temp_storage(video_bytes: bytes) -> str:
    """Uploads video bytes to a temporary file host and returns the public URL."""
    try:
        files = {'file': ('video.mp4', video_bytes, 'video/mp4')}
        response = requests.post('https://tmpfiles.org/api/v1/upload', files=files, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to upload video to temporary storage: {e}")
        return None

def _compress_video_if_needed(video_bytes: bytes, max_size_mb: int = 15) -> bytes:
    """Checks video size and compresses it if it exceeds the max size."""
    max_size_bytes = max_size_mb * 1024 * 1024
    if len(video_bytes) <= max_size_bytes:
        logger.info("Video is within size limits. No compression needed.")
        return video_bytes

    logger.info(f"Video size ({len(video_bytes) / 1024 / 1024:.2f}MB) exceeds {max_size_mb}MB. Compressing...")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_in:
        temp_in.write(video_bytes)
        input_path = temp_in.name

    output_path = f"{input_path.rsplit('.', 1)[0]}_compressed.mp4"
    
    try:
        video_clip = VideoFileClip(input_path)
        video_clip.write_videofile(output_path, bitrate="1M", logger=None)
        video_clip.close()
        with open(output_path, "rb") as f:
            compressed_bytes = f.read()
        logger.info(f"Video compressed. New size: {len(compressed_bytes) / 1024 / 1024:.2f}MB")
        return compressed_bytes
    except Exception as e:
        logger.error(f"Failed to compress video: {e}")
        return video_bytes
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

def _send_whatsapp_message(to: str, message: str = None, media_url: str = None):
    """Sends a message (text or media) via Twilio."""
    if not twilio_client:
        logger.error("Twilio client not available.")
        return
    try:
        message_payload = {
            'from_': f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
            'to': f'whatsapp:{to}'
        }
        if message:
            message_payload['body'] = message
        if media_url:
            message_payload['media_url'] = [media_url]

        twilio_client.messages.create(**message_payload)
        log_msg = f"Message send request accepted by Twilio for {to}."
        if media_url:
            log_msg = f"Video send request accepted by Twilio for {to}."
        logger.info(log_msg)

    except TwilioRestException as e:
        logger.error(f"Twilio API Error sending message to {to}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred sending WhatsApp message to {to}: {e}")

# --- Core Background Task for WhatsApp Video Generation ---
async def generate_video_task(user_phone_number: str, original_prompt: str, enhanced_prompt: str, style: str):
    """The main background task for generating and sending a video for the WhatsApp bot."""
    success = False
    loop = asyncio.get_running_loop()
    try:
        await _send_whatsapp_message_async(to=user_phone_number, message="🤖 The AI is working its magic... This can take a minute.")
        
        client = InferenceClient(provider="fal-ai", token=settings.HUGGING_FACE_API_KEY)
        
        video_bytes = await loop.run_in_executor(
            None,
            lambda: client.text_to_video(
                enhanced_prompt, 
                model="Wan-AI/Wan2.2-T2V-A14B"
            )
        )
        
        await _send_whatsapp_message_async(to=user_phone_number, message="⬆️ Compressing and preparing your video file...")
        
        compressed_bytes = await loop.run_in_executor(None, _compress_video_if_needed, video_bytes)
        media_url = await loop.run_in_executor(None, _upload_video_to_temp_storage, compressed_bytes)

        if not media_url:
            raise Exception("Failed to upload video to temporary storage.")

        caption = f"✅ Here's your '{style}' video!\n\n*Prompt:* _{original_prompt}_"
        await _send_whatsapp_message_async(to=user_phone_number, message=caption, media_url=media_url)
        
        await save_generation_history(user_phone_number, original_prompt, style, media_url)
        success = True

    except HfHubHTTPError as e:
        logger.error(f"Hugging Face API Error for {user_phone_number}: {e}")
        await _send_whatsapp_message_async(user_phone_number, f"Sorry, the AI model is currently busy or unavailable. Details: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred for {user_phone_number}: {e}")
        await _send_whatsapp_message_async(user_phone_number, "😔 Apologies, something went wrong on my end. Please try again later.")
    finally:
        logger.info(f"Background task finished for {user_phone_number}. Success: {success}")
        await clear_user_state(user_phone_number)

# --- WebSocket Video Generation (for Web App) ---
async def generate_video_for_websocket(prompt: str, style: str, websocket: WebSocket):
    """Handles video generation for the web app via WebSockets, ensuring it remains functional."""
    loop = asyncio.get_running_loop()
    try:
        # The web app uses a simpler prompt enhancement logic with default styles
        style_prefix = llm_service.DEFAULT_STYLES.get(style, "")
        full_prompt = f"{style_prefix} {prompt}".strip()
        logger.info(f"WebSocket - Enhanced prompt: {full_prompt}")

        cache_key = f"{style}:{prompt}"
        if cache_key in video_cache:
            logger.info(f"WebSocket cache hit for: {cache_key}")
            await websocket.send_json({"video": video_cache[cache_key]})
            return

        await websocket.send_json({"status": "Generating video..."})

        client = InferenceClient(provider="fal-ai", token=settings.HUGGING_FACE_API_KEY)

        video_bytes = await loop.run_in_executor(
            None,
            lambda: client.text_to_video(
                full_prompt, 
                model="Wan-AI/Wan2.2-T2V-A14B"
            )
        )
        
        await websocket.send_json({"status": "Encoding video..."})
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')
        
        video_cache[cache_key] = video_base64 # Save to in-memory cache
        await websocket.send_json({"video": video_base64})

    except HfHubHTTPError as e:
        logger.error(f"Hugging Face API Error for WebSocket: {e}")
        await websocket.send_json({"error": "AI model is busy. Please try again."})
    except Exception as e:
        logger.error(f"An unexpected error occurred for WebSocket: {e}")
        await websocket.send_json({"error": "An internal server error occurred."})

async def _send_whatsapp_message_async(to: str, message: str = None, media_url: str = None):
    """Asynchronously sends a message."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _send_whatsapp_message, to, message, media_url)

