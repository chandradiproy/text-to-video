# backend/app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import endpoints, whatsapp_router # Import the new router
from .db.database import connect_to_mongo, close_mongo_connection # Import DB functions

# --- Lifespan Event Handler ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events. Connects to the database on startup
    and disconnects on shutdown.
    """
    print("Application startup...")
    await connect_to_mongo()
    yield
    print("Application shutdown...")
    await close_mongo_connection()

# Initialize the FastAPI application with the lifespan handler
app = FastAPI(
    title="AI Video Generation API",
    description="A backend service to generate videos from text prompts.",
    version="2.0.0", # Updated for Round 2
    lifespan=lifespan
)

# --- CORS (Cross-Origin Resource Sharing) Middleware ---
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    # Add your deployed frontend URLs here for production
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
app.include_router(whatsapp_router.router, prefix="/api/v1/bot", tags=["WhatsApp Bot"])

# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to the AI Video Generation API V2!"}

