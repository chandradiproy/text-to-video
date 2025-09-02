import asyncio
from fastapi import APIRouter, Form, BackgroundTasks
from twilio.rest import Client
from ..core.config import settings
from ..services import video_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Twilio Client
try:
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    logger.info("Twilio client initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Twilio client: {e}")
    client = None

def send_whatsapp_message(to: str, message: str):
    """Helper function to send a WhatsApp message."""
    if not client:
        logger.error("Twilio client not available. Cannot send message.")
        return
    try:
        client.messages.create(
            from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
            body=message,
            to=f'whatsapp:{to}'
        )
        logger.info(f"Message sent to {to}: '{message}'")
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message to {to}: {e}")

# --- NEW: Synchronous wrapper for our async background task ---
def run_video_generation_task(prompt: str, style: str, user_phone_number: str):
    """
    This synchronous function can be safely passed to BackgroundTasks.
    It uses asyncio.run() to execute our main async service function.
    """
    logger.info(f"Starting background task for {user_phone_number}")
    try:
        asyncio.run(video_service.generate_video_for_whatsapp(prompt, style, user_phone_number))
        logger.info(f"Background task for {user_phone_number} completed.")
    except Exception as e:
        logger.error(f"Error in background task for {user_phone_number}: {e}")


@router.post("/webhook/twilio")
async def twilio_webhook(
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(...)
):
    """
    This endpoint receives incoming WhatsApp messages from Twilio.
    """
    user_phone_number = From.replace('whatsapp:', '')
    prompt = Body.strip()
    logger.info(f"Received message from {user_phone_number}: '{prompt}'")

    # Command System & Input Validation
    if prompt.lower().startswith('/help'):
        help_message = "Welcome! To generate a video, send a descriptive prompt (e.g., 'a robot dancing in the rain')."
        send_whatsapp_message(to=user_phone_number, message=help_message)
        return {"status": "help message sent"}

    if len(prompt) < 10:
        error_message = "🤔 Your prompt seems too short. Try something more descriptive!"
        send_whatsapp_message(to=user_phone_number, message=error_message)
        return {"status": "prompt too short"}

    # Acknowledge receipt
    ack_message = "🎬 Got it! Generating your video... This can take a minute or two."
    send_whatsapp_message(to=user_phone_number, message=ack_message)

    # --- FIX: Call the synchronous wrapper in the background task ---
    background_tasks.add_task(
        run_video_generation_task,
        prompt,
        "Default",
        user_phone_number
    )

    return {"status": "message received and processing in background"}

