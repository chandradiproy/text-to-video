# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import endpoints

# Initialize the FastAPI application
app = FastAPI(
    title="AI Video Generation API",
    description="A backend service to generate videos from text prompts using Stability AI.",
    version="1.0.0"
)

# --- CORS (Cross-Origin Resource Sharing) Middleware ---
# This is crucial for allowing your React frontend to communicate with this backend.
# Be sure to update the origins to match your deployed frontend URL in production.
origins = [
    "http://localhost:5173",  # For local React development
    # "https://your-vercel-frontend-app.vercel.app", # Add your deployed frontend URL here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


# --- Include API Routers ---
# This adds the endpoints defined in endpoints.py to the main application,
# prefixing them with /api/v1
app.include_router(endpoints.router, prefix="/api/v1")


# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    return {"message": "Welcome to the AI Video Generation API!"}

# uvicorn app.main:app --reload
