# backend/app/api/whatsapp_router.py

import asyncio
import logging
import re
from fastapi import APIRouter, Form, BackgroundTasks

from ..db.database import (
    get_user_state, set_user_state, clear_user_state, 
    get_user_history, create_custom_style, get_user_styles, delete_custom_style,
    find_cached_video, find_styles_for_prompt
)
from ..services import video_service, llm_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# --- Helper to send messages ---
async def send_whatsapp_message_async(to: str, message: str = None, media_url: str = None):
    """Asynchronously sends a message via Twilio, handling both text and media."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, video_service._send_whatsapp_message, to, message, media_url)

# --- Main Webhook Endpoint ---
@router.post("/webhook/twilio")
async def twilio_webhook(
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(...)
):
    user_phone_number = From.replace('whatsapp:', '')
    prompt = Body.strip()
    logger.info(f"Received message from {user_phone_number}: '{prompt}'")

    user_state_doc = await get_user_state(user_phone_number) or {}
    user_state = user_state_doc.get("state")
    user_data = user_state_doc.get("data", {})
    
    # --- 1. Universal Commands (Processed first, regardless of state) ---
    if prompt.lower().startswith('/'):
        if prompt.lower() == '/help':
            help_message = (
                "Welcome to the AI Video Bot! 🤖\n\n"
                "To create a video, just send a descriptive prompt.\n\n"
                "*COMMANDS:*\n"
                "*/status* - Check if a video is being generated.\n"
                "*/history* - View your last 5 videos.\n"
                "*/styles* - List your custom styles.\n"
                "*/createstyle <name> \"<prompt>\"* - Create a new style.\n"
                "*/deletestyle <name>* - Delete a custom style.\n"
                "*/cancel* - Cancel the current operation.\n"
                "*/help* - Show this message."
            )
            await send_whatsapp_message_async(to=user_phone_number, message=help_message)
            return {"status": "help message sent"}
        
        elif prompt.lower() == '/cancel':
            if user_state:
                await clear_user_state(user_phone_number)
                await send_whatsapp_message_async(to=user_phone_number, message="✅ Operation cancelled.")
            else:
                await send_whatsapp_message_async(to=user_phone_number, message="Nothing to cancel.")
            return {"status": "cancel command processed"}

        elif prompt.lower() == '/status':
            if user_state == "processing_video":
                await send_whatsapp_message_async(to=user_phone_number, message="⏳ Your video is currently being generated. Please wait.")
            else:
                await send_whatsapp_message_async(to=user_phone_number, message="✅ You have no active video generation. Send a prompt to start!")
            return {"status": "status checked"}

        elif prompt.lower() == '/history':
            history = await get_user_history(user_phone_number)
            if not history:
                await send_whatsapp_message_async(user_phone_number, "You have no video history yet.")
            else:
                response = "📜 *Your Last 5 Videos:*\n\n"
                for i, record in enumerate(history):
                    ts = record['timestamp'].strftime("%b %d, %H:%M UTC")
                    response += f"*{i+1}. Prompt:* `{record['prompt']}`\n   - *Style:* {record['style']}\n   - *When:* {ts}\n   - *Link:* {record['media_url']}\n\n"
                await send_whatsapp_message_async(user_phone_number, response)
            return {"status": "history sent"}

        elif prompt.lower() == '/styles':
            styles = await get_user_styles(user_phone_number)
            if not styles:
                await send_whatsapp_message_async(user_phone_number, "You haven't created any custom styles yet. Use `/createstyle` to make one!")
            else:
                response = "🎨 *Your Custom Styles:*\n\n"
                for style in styles:
                    response += f"*- Name:* `{style['style_name']}`\n   *- Prompt:* \"{style['style_prompt']}\"\n\n"
                await send_whatsapp_message_async(user_phone_number, response)
            return {"status": "styles sent"}

        elif prompt.lower().startswith('/createstyle'):
            match = re.match(r'/createstyle\s+(\w+)\s+"([^"]+)"', prompt, re.IGNORECASE)
            if not match:
                await send_whatsapp_message_async(user_phone_number, 'Invalid format. Use: /createstyle <name> "<style prompt>"')
                return {"status": "createstyle format error"}
            style_name, style_prompt_text = match.groups()
            await create_custom_style(user_phone_number, style_name, style_prompt_text)
            success_message = f"✅ Style '{style_name}' created successfully!"
            
            if user_state in ['awaiting_style_choice', 'awaiting_cached_style_choice'] and user_data.get('prompt'):
                original_prompt = user_data['prompt']
                success_message += f"\n\nNow generating your video for '{original_prompt}' with this new style!"
                await send_whatsapp_message_async(user_phone_number, success_message)
                
                user_styles = await get_user_styles(user_phone_number)
                enhanced_prompt = llm_service.get_final_prompt(original_prompt, style_name, user_styles)
                
                await set_user_state(user_phone_number, "processing_video")
                background_tasks.add_task(video_service.generate_video_task, user_phone_number, original_prompt, enhanced_prompt, style_name)
            else:
                 await send_whatsapp_message_async(user_phone_number, success_message)
            return {"status": "style created"}

        elif prompt.lower().startswith('/deletestyle'):
            parts = prompt.split()
            if len(parts) != 2:
                await send_whatsapp_message_async(user_phone_number, 'Invalid format. Use: /deletestyle <name>')
                return {"status": "deletestyle format error"}
            style_name = parts[1]
            deleted = await delete_custom_style(user_phone_number, style_name)
            if deleted:
                await send_whatsapp_message_async(user_phone_number, f"🗑️ Style '{style_name}' deleted.")
            else:
                await send_whatsapp_message_async(user_phone_number, f"❌ Could not find a style named '{style_name}'.")
            return {"status": "style deleted"}

    # --- 2. State-Based Logic ---
    if user_state == 'awaiting_cached_style_choice':
        original_prompt = user_data['prompt']
        cached_styles = user_data.get('cached_styles', [])
        
        if prompt.lower() == 'all':
            await set_user_state(user_phone_number, 'awaiting_style_choice', {"prompt": original_prompt})
            # Fall through to the next block by re-assigning user_state
            user_state = 'awaiting_style_choice'
        elif prompt.isdigit():
            try:
                choice_index = int(prompt) - 1
                if 0 <= choice_index < len(cached_styles):
                    chosen_style = cached_styles[choice_index]
                    cached_video = await find_cached_video(user_phone_number, original_prompt, chosen_style)
                    await send_whatsapp_message_async(user_phone_number, "✅ Found it! Here's your video from the cache.", media_url=cached_video['media_url'])
                    await clear_user_state(user_phone_number)
                    return {"status": "cached video sent"}
                else: raise ValueError("Choice out of range")
            except (ValueError, IndexError):
                await send_whatsapp_message_async(user_phone_number, "That's not a valid choice. Please pick a number from the list, or reply 'all'.")
                return {"status": "invalid cached style choice"}
        else:
            await clear_user_state(user_phone_number)
            await send_whatsapp_message_async(user_phone_number, "Let's start over. Please send your new prompt.")
            return {"status": "state cleared"}

    if user_state == 'awaiting_style_choice':
        if prompt.isdigit():
            try:
                choice_index = int(prompt) - 1
                style_options = user_data.get('style_options', [])
                if 0 <= choice_index < len(style_options):
                    chosen_style = style_options[choice_index]
                    original_prompt = user_data['prompt']
                    
                    cached_video = await find_cached_video(user_phone_number, original_prompt, chosen_style)
                    if cached_video:
                        await send_whatsapp_message_async(user_phone_number, "✅ Found it! Here's your video from the cache.", media_url=cached_video['media_url'])
                        await clear_user_state(user_phone_number)
                        return {"status": "cached video sent after choice"}

                    await send_whatsapp_message_async(user_phone_number, f"Great! Generating a '{chosen_style}' video for you. This might take a minute.")
                    user_styles = await get_user_styles(user_phone_number)
                    enhanced_prompt = llm_service.get_final_prompt(original_prompt, chosen_style, user_styles)
                    
                    await set_user_state(user_phone_number, "processing_video")
                    background_tasks.add_task(video_service.generate_video_task, user_phone_number, original_prompt, enhanced_prompt, chosen_style)
                    return {"status": "video generation started after style choice"}
                else:
                    raise ValueError("Choice out of range")
            except (ValueError, IndexError):
                await send_whatsapp_message_async(user_phone_number, "That's not a valid number. Please pick one from the list or send /cancel.")
                return {"status": "invalid style choice"}
        else:
            await clear_user_state(user_phone_number)
            await send_whatsapp_message_async(user_phone_number, "Looks like you want to start over. Your previous operation was cancelled. Please send your new prompt again.")
            return {"status": "state cleared, awaiting new prompt"}

    # --- 3. Handle New Prompts ---
    if len(prompt) < 10:
        await send_whatsapp_message_async(user_phone_number, "🤔 Your prompt is a bit short. Try being more descriptive!")
        return {"status": "prompt too short"}
    
    cached_styles = await find_styles_for_prompt(user_phone_number, prompt)
    if cached_styles:
        response = "I've made videos for that prompt before with these styles:\n\n"
        for i, style in enumerate(cached_styles):
            response += f"*{i+1}.* {style.capitalize()}\n"
        response += "\nReply with a number to get that video, or reply with *'all'* to see all available style options."
        await set_user_state(user_phone_number, 'awaiting_cached_style_choice', {"prompt": prompt, "cached_styles": cached_styles})
        await send_whatsapp_message_async(user_phone_number, response)
        return {"status": "offering cached styles"}

    user_styles = await get_user_styles(user_phone_number)
    llm_analysis = await llm_service.analyze_prompt_with_groq(prompt, user_styles)

    if llm_analysis.get("requires_user_choice"):
        style_options = list(llm_service.DEFAULT_STYLES.keys())
        custom_styles = await get_user_styles(user_phone_number)
        if custom_styles:
            style_options.extend([s['style_name'] for s in custom_styles])
        
        bot_response = "I couldn't detect a specific style. Please choose one to continue:\n\n"
        for i, style in enumerate(style_options):
            bot_response += f"*{i+1}.* {style}\n"
        bot_response += "\nOr, create your own with the `/createstyle` command!"

        await set_user_state(user_phone_number, 'awaiting_style_choice', {"prompt": prompt, "style_options": style_options})
        await send_whatsapp_message_async(user_phone_number, bot_response)
        return {"status": "awaiting style choice"}
    else:
        style = llm_analysis["style"]
        enhanced_prompt = llm_analysis["enhanced_prompt"]
        
        cached_video = await find_cached_video(user_phone_number, prompt, style)
        if cached_video:
            await send_whatsapp_message_async(user_phone_number, "✅ Found it! Here's your video from the cache.", media_url=cached_video['media_url'])
            return {"status": "cached video sent directly"}

        await send_whatsapp_message_async(user_phone_number, f"Got it! I have enough info to start. Generating your video now...")
        await set_user_state(user_phone_number, "processing_video")
        background_tasks.add_task(video_service.generate_video_task, user_phone_number, prompt, enhanced_prompt, style)
        return {"status": "video generation started directly"}

