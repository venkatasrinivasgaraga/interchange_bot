import os
import re
import json
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# Bot Configuration
API_ID = "your_api_id"
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"

# File to store user preferences
USER_SETTINGS_FILE = "user_settings.json"

# Load or initialize user settings
if os.path.exists(USER_SETTINGS_FILE):
    with open(USER_SETTINGS_FILE, "r") as f:
        user_settings = json.load(f)
else:
    user_settings = {}

# Initialize bot
app = Client("FileRenameBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to rename files
def rename_file(filename):
    prefix = "[@Animes2u] "
    
    # Remove unwanted bracketed text except [E78], [720p]
    cleaned_name = re.sub(r"(?!E\d+|\d+p)[^]+", "", filename)

    # Remove @mentions (inside and outside brackets)
    cleaned_name = re.sub(r"@\S+", "", cleaned_name).strip()

    # Ensure there's only one space between words
    cleaned_name = re.sub(r"\s+", " ", cleaned_name).strip()

    # Add prefix at the start
    renamed_file = prefix + cleaned_name
    return renamed_file

# Start command
@app.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text(
        "Welcome to the File Rename Bot!\n\n"
        "📌 Send me a file, and I will rename it automatically.\n"
        "📌 Use /pause to stop renaming and /resume to enable it.\n"
        "📌 Send /setthumb with an image to save a permanent thumbnail.\n"
        "📌 Send /delthumb to delete the saved thumbnail.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Source Code", url="https://github.com")]]
        ),
    )

# Pause renaming
@app.on_message(filters.command("pause"))
async def pause_renaming(client, message):
    user_id = str(message.from_user.id)
    user_settings[user_id] = user_settings.get(user_id, {})
    user_settings[user_id]["paused"] = True
    with open(USER_SETTINGS_FILE, "w") as f:
        json.dump(user_settings, f)
    await message.reply_text("✅ File renaming is now **paused**.")

# Resume renaming
@app.on_message(filters.command("resume"))
async def resume_renaming(client, message):
    user_id = str(message.from_user.id)
    user_settings[user_id] = user_settings.get(user_id, {})
    user_settings[user_id]["paused"] = False
    with open(USER_SETTINGS_FILE, "w") as f:
        json.dump(user_settings, f)
    await message.reply_text("✅ File renaming is now **enabled**.")

# Set permanent thumbnail
@app.on_message(filters.command("setthumb") & filters.photo)
async def set_thumbnail(client, message):
    user_id = str(message.from_user.id)
    file_id = message.photo.file_id
    user_settings[user_id] = user_settings.get(user_id, {})
    user_settings[user_id]["thumbnail"] = file_id
    with open(USER_SETTINGS_FILE, "w") as f:
        json.dump(user_settings, f)
    await message.reply_text("✅ Thumbnail has been **saved**.")

# Delete saved thumbnail
@app.on_message(filters.command("delthumb"))
async def delete_thumbnail(client, message):
    user_id = str(message.from_user.id)
    if user_id in user_settings and "thumbnail" in user_settings[user_id]:
        del user_settings[user_id]["thumbnail"]
        with open(USER_SETTINGS_FILE, "w") as f:
            json.dump(user_settings, f)
        await message.reply_text("✅ Thumbnail has been **deleted**.")
    else:
        await message.reply_text("⚠️ No thumbnail was set.")

# Handle file renaming
@app.on_message(filters.document | filters.video)
async def rename_and_send_file(client, message):
    user_id = str(message.from_user.id)

    # Check if renaming is paused
    if user_id in user_settings and user_settings[user_id].get("paused", False):
        await message.reply_text("⏸ File renaming is currently **paused**. Use /resume to enable it.")
        return

    # Get original file name
    file_name = message.document.file_name if message.document else message.video.file_name
    new_filename = rename_file(file_name)

    # Check if a thumbnail is set
    thumb_id = user_settings.get(user_id, {}).get("thumbnail")

    # Download the file temporarily
    file_path = await message.download()

    # Send the renamed file
    await message.reply_document(
        document=file_path,
        file_name=new_filename,
        thumb=thumb_id,
        caption=f"✅ File renamed to: **{new_filename}**",
    )

    # Delete the downloaded file to save space
    os.remove(file_path)

# Run the bot
app.run()
