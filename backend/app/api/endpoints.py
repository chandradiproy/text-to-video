from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.video_service import generate_video_from_prompt

router = APIRouter()

class VideoRequest(BaseModel):
    prompt: str

class VideoResponse(BaseModel):
    image: str # base64 encoded image
    video: str # base64 encoded video

@router.post("/generate-video", response_model=VideoResponse)
async def create_video(request: VideoRequest):
    """
    Endpoint to generate a video from a text prompt.
    It calls the video generation service and returns the result.
    """
    try:
        print(f"Received request to generate video for prompt: '{request.prompt}'")
        # The 'await' keyword is crucial here for async functions
        result = await generate_video_from_prompt(request.prompt)
        print("Successfully generated video. Returning data.")
        return result
    except HTTPException as e:
        # Re-raise HTTP exceptions from the service layer
        raise e
    except Exception as e:
        print(f"An unexpected error occurred during video generation: {e}")
        # Handle any other unexpected errors
        raise HTTPException(status_code=500, detail=str(e))
