from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.video_service import generate_video_from_prompt

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    A simple endpoint to check if the server is running.
    Used to "wake up" the service from a cold start.
    """
    return {"status": "ok"}


@router.websocket("/ws/generate-video")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time video generation.
    Receives a prompt and style, then streams status updates and the final video.
    """
    await websocket.accept()
    try:
        while True:
            # Wait for a message from the client (prompt and style)
            data = await websocket.receive_json()
            
            prompt = data.get("prompt")
            style = data.get("style")

            if prompt and style:
                # Call the service function to handle the generation process
                await generate_video_from_prompt(prompt, style, websocket)
            else:
                await websocket.send_json({"error": "Prompt and style are required."})

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        error_message = f"An error occurred in the WebSocket endpoint: {e}"
        print(error_message)
        try:
            # Attempt to send an error message before closing if the socket is still open
            await websocket.send_json({"error": f"A server error occurred: {e}"})
        except Exception as send_error:
            print(f"Failed to send error message to client: {send_error}")

