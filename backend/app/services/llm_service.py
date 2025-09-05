# backend/app/services/llm_service.py

import asyncio
import logging
import json
from groq import Groq, AsyncGroq
from ..core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pre-defined styles ---
DEFAULT_STYLES = {
    "Cinematic": "cinematic, dramatic lighting, high detail, 4k, film grain, ",
    "Anime": "anime style, key visual, vibrant, studio ghibli, cel shading, ",
    "Pixel Art": "pixel art, 16-bit, retro, low-res, vibrant colors, ",
    "Documentary": "documentary style, realistic, natural lighting, steady cam, ",
    "Fantasy": "fantasy, epic, magical, high detail, intricate, glowing, ",
    "Sci-Fi": "sci-fi, futuristic, high-tech, neon lights, dystopian, "
}

def get_final_prompt(original_prompt: str, style_name: str, user_styles: list = None):
    """Constructs the final, enhanced prompt string."""
    user_styles_dict = {s['style_name']: s['style_prompt'] for s in user_styles} if user_styles else {}
    
    style_prefix = DEFAULT_STYLES.get(style_name, user_styles_dict.get(style_name, ""))
    
    return f"{style_prefix}{original_prompt}".strip()

async def analyze_prompt_with_groq(prompt: str, user_styles: list = None):
    """
    Uses Groq LLM to analyze a prompt, determine if a style is present,
    and decide the next step for the bot.
    """
    if not settings.GROQ_API_KEY:
        logger.error("GROQ_API_KEY not configured.")
        return { "requires_user_choice": True }

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    
    all_styles = list(DEFAULT_STYLES.keys())
    if user_styles:
        all_styles.extend([s['style_name'] for s in user_styles])

    system_prompt = f"""
    You are an AI assistant for a text-to-video bot. Your task is to analyze a user's prompt.
    You must determine if the prompt already contains a clear artistic style.
    The available styles are: {', '.join(all_styles)}.

    Respond ONLY with a JSON object with the following structure:
    {{
      "style_detected": "Name of the detected style or null",
      "reasoning": "A brief explanation of why you detected that style or why you couldn't.",
      "enhanced_prompt": "A slightly improved, more vivid version of the original prompt, incorporating the detected style if any."
    }}

    If the prompt is generic (e.g., "a dog running"), the style should be null.
    If the prompt is "a dog running in a cinematic style", you must detect "Cinematic".
    Be precise. Only detect a style if it's explicitly mentioned or very strongly implied.
    """

    try:
        logger.info(f"Calling Groq API to analyze prompt: '{prompt}'")
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            model="llama-3.1-8b-instant",
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        
        response_text = chat_completion.choices[0].message.content
        logger.info(f"Received Groq API raw response: {response_text}")
        analysis = json.loads(response_text)

        detected_style = analysis.get("style_detected")

        if detected_style and detected_style in all_styles:
            logger.info(f"LLM detected style: '{detected_style}'. Proceeding directly to generation.")
            final_prompt = get_final_prompt(prompt, detected_style, user_styles)
            return {
                "requires_user_choice": False,
                "style": detected_style,
                "enhanced_prompt": final_prompt
            }
        else:
            logger.info("LLM did not detect a clear style. Asking user for choice.")
            return { "requires_user_choice": True }

    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        # --- FIX: Fallback now also indicates it needs a user choice ---
        return { "requires_user_choice": True }

