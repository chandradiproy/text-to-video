# backend/app/db/database.py

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from ..core.config import settings
from datetime import datetime, timezone
import certifi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client: AsyncIOMotorClient = None
db = None

# --- Connection Management ---

async def connect_to_mongo():
    global client, db
    logger.info("Connecting to MongoDB Atlas...")
    try:
        if not settings.MONGODB_URI:
            raise ValueError("MongoDB URI not configured")
        
        client = AsyncIOMotorClient(settings.MONGODB_URI, tlsCAFile=certifi.where())
        db = client.get_database("video_bot_db")
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB Atlas.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        client = None
        db = None
        raise

async def close_mongo_connection():
    global client
    if client:
        logger.info("Closing MongoDB connection.")
        client.close()

# --- State Management Functions ---

async def set_user_state(user_phone_number: str, state: str, data: dict = None):
    """Saves or updates the user's current conversational state."""
    if db is None:
        logger.error("Database is not connected. Cannot set user state.")
        return
    
    state_collection = db["user_states"]
    update_doc = {"$set": {"state": state, "data": data or {}, "updated_at": datetime.now(timezone.utc)}}
    
    try:
        await state_collection.update_one(
            {"user_phone_number": user_phone_number},
            update_doc,
            upsert=True
        )
        logger.info(f"Set state for {user_phone_number} to '{state}' with data: {data}")
    except Exception as e:
        logger.error(f"Failed to set state for {user_phone_number}: {e}")

async def get_user_state(user_phone_number: str):
    """Retrieves the user's current conversational state."""
    if db is None:
        return None
    state_collection = db["user_states"]
    return await state_collection.find_one({"user_phone_number": user_phone_number})

async def clear_user_state(user_phone_number: str):
    """Clears the user's state."""
    await set_user_state(user_phone_number, None, {})
    logger.info(f"Cleared state for {user_phone_number}")

# --- History & Cache Management ---

async def save_generation_history(user_phone_number: str, prompt: str, style: str, media_url: str):
    """Saves a record of a video generation."""
    if db is None: return
    history_collection = db["history"]
    document = {
        "user_phone_number": user_phone_number,
        "prompt": prompt,
        "style": style.lower(),
        "media_url": media_url,
        "timestamp": datetime.now(timezone.utc)
    }
    await history_collection.insert_one(document)
    logger.info(f"Saved generation history for user {user_phone_number}")

async def get_user_history(user_phone_number: str, limit: int = 5):
    """Retrieves the most recent generation history."""
    if db is None: return []
    history_collection = db["history"]
    cursor = history_collection.find({"user_phone_number": user_phone_number}).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(length=limit)

async def find_cached_video(user_phone_number: str, prompt: str, style: str):
    """Finds a specific video by prompt and style."""
    if db is None: return None
    history_collection = db["history"]
    return await history_collection.find_one(
        {"user_phone_number": user_phone_number, "prompt": prompt, "style": style.lower()},
        sort=[("timestamp", -1)]
    )

async def find_styles_for_prompt(user_phone_number: str, prompt: str):
    """Finds all unique styles a user has previously used for a specific prompt."""
    if db is None: return []
    history_collection = db["history"]
    # Use an aggregation pipeline to find distinct styles for the prompt
    pipeline = [
        {"$match": {"user_phone_number": user_phone_number, "prompt": prompt}},
        {"$group": {"_id": "$style"}},
        {"$sort": {"_id": 1}}
    ]
    cursor = history_collection.aggregate(pipeline)
    styles = await cursor.to_list(length=100)
    return [s["_id"] for s in styles]


# --- Custom Style Management ---

async def create_custom_style(user_phone_number: str, style_name: str, style_prompt: str):
    """Creates or updates a user-defined custom style."""
    if db is None: return
    styles_collection = db["custom_styles"]
    await styles_collection.update_one(
        {"user_phone_number": user_phone_number, "style_name": style_name.lower()},
        {"$set": {"style_prompt": style_prompt, "updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )

async def get_user_styles(user_phone_number: str):
    """Retrieves all custom styles for a specific user."""
    if db is None: return []
    styles_collection = db["custom_styles"]
    cursor = styles_collection.find({"user_phone_number": user_phone_number})
    return await cursor.to_list(length=100)

async def delete_custom_style(user_phone_number: str, style_name: str):
    """Deletes a user-defined custom style."""
    if db is None: return False
    styles_collection = db["custom_styles"]
    result = await styles_collection.delete_one({"user_phone_number": user_phone_number, "style_name": style_name.lower()})
    return result.deleted_count > 0

