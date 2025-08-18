import base64
from fastapi import HTTPException
from app.core.config import settings
from huggingface_hub import InferenceClient

async def generate_video_from_prompt(prompt: str):
    """
    Generates a video from a text prompt using the Hugging Face InferenceClient
    with a specific provider (fal-ai).
    """
    if not settings.HUGGING_FACE_API_KEY:
        raise HTTPException(status_code=500, detail="HUGGING_FACE_API_KEY is not configured.")

    api_key = settings.HUGGING_FACE_API_KEY
    
    print("Initializing InferenceClient with fal-ai provider...")

    try:
        # Initialize the client with the specified provider and your API token
        client = InferenceClient(
            provider="fal-ai",
            token=api_key,
        )

        print("Sending prompt to fal-ai with model Wan-AI/Wan2.2-T2V-A14B...")
        
        # Call the text_to_video method with the prompt and model
        video_bytes = client.text_to_video(
            prompt,
            model="Wan-AI/Wan2.2-T2V-A14B",
        )

        print("Received video data, encoding response...")
        
        # Encode the raw video bytes to base64 for the JSON response
        video_base64 = base64.b64encode(video_bytes).decode("utf-8")

        return {
            "video": video_base64,
            "image": "" # No image is generated in this workflow
        }

    except Exception as e:
        # Catch any exceptions during the API call and return a detailed error
        error_message = f"An error occurred during video generation with fal-ai: {e}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)
