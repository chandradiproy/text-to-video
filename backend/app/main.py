# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import endpoints, whatsapp_router # Import the new router

# Initialize the FastAPI application
app = FastAPI(
    title="AI Video Generation API",
    description="A backend service to generate videos from text prompts and a WhatsApp bot.",
    version="2.0.0"
)

# --- CORS Middleware (for the web frontend) ---
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    # Add your deployed frontend URL here for production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include API Routers ---
app.include_router(endpoints.router, prefix="/api/v1", tags=["Web App"])
app.include_router(whatsapp_router.router, prefix="/api/v1/bot", tags=["WhatsApp Bot"]) # Add the new router

# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    return {"message": "Welcome to the AI Video Generation API!"}


# uvicorn app.main:app --reload
