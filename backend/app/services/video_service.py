import base64
import asyncio
from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect
from huggingface_hub import InferenceClient
# from huggingface_hub.inference._text_to_video import TextToVideoError
from app.core.config import settings

# In-memory cache to store generated videos.
video_cache = {}

# Pre-defined style prefixes to enhance user prompts (RAG-style improvement).
STYLE_PREFIXES = {
    "Default": "",
    "Cinematic": "cinematic, dramatic lighting, high detail, 4k, epic,",
    "Anime": "anime style, vibrant colors, cel-shaded, japanese animation,",
    "Pixel Art": "pixel art style, 16-bit, retro gaming aesthetic,",
    "Documentary": "documentary style, realistic, natural lighting,",
    "Fantasy": "fantasy style, magical, ethereal, enchanted,",
    "Sci-Fi": "sci-fi, futuristic, high-tech, neon lights,"
}

async def generate_video_from_prompt(prompt: str, style: str, websocket: WebSocket):
    """
    Generates a video from a prompt, with style enhancement, caching, and WebSocket status updates.
    """
    if not settings.HUGGING_FACE_API_KEY:
        await websocket.send_json({"error": "HUGGING_FACE_API_KEY is not configured."})
        return

    style_prefix = STYLE_PREFIXES.get(style, "")
    full_prompt = f"{style_prefix} {prompt}"
    cache_key = f"{style}:{prompt}"
    
    await websocket.send_json({"status": f"Enhanced prompt: '{full_prompt[:100]}...'"})
    await asyncio.sleep(1)

    if cache_key in video_cache:
        print(f"Cache hit for prompt: {prompt}")
        await websocket.send_json({"status": "Found in cache! Returning previously generated video."})
        await asyncio.sleep(1)
        await websocket.send_json(video_cache[cache_key])
        return

    print(f"Cache miss for prompt: {prompt}. Calling API.")
    
    try:
        await websocket.send_json({"status": "Initializing AI model..."})
        client = InferenceClient(provider="fal-ai", token=settings.HUGGING_FACE_API_KEY)

        await websocket.send_json({"status": "Generating video... This can take a minute."})
        video_bytes = client.text_to_video(
            full_prompt,
            model="Wan-AI/Wan2.2-T2V-A14B",
        )

        await websocket.send_json({"status": "Encoding video..."})
        video_base64 = base64.b64encode(video_bytes).decode("utf-8")
        
        response_data = {
            "video": video_base64,
            "image": ""
        }
        
        video_cache[cache_key] = response_data
        
        await websocket.send_json({"status": "Video generated successfully!"})
        await asyncio.sleep(1)
        await websocket.send_json(response_data)

    except Exception as e:
        # --- ERROR HANDLING FOR 402 PAYMENT REQUIRED ---
        error_str = str(e)
        if "402 Client Error: Payment Required" in error_str:
            error_message = "API credit limit reached. Please upgrade your Hugging Face plan or try again later."
        else:
            error_message = f"An error occurred during video generation: {e}"
        
        print(error_message)
        await websocket.send_json({"error": error_message})
