import os
import asyncio
import re
from pyrogram import Client, filters, idle
from flask import Flask
from threading import Thread

# Load environment variables
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEFAULT_KEYWORD = "[@Animes2u] "

# Ensure required environment variables are set
if not API_ID or not API_HASH or not BOT_TOKEN:
    raise ValueError("❌ Missing API_ID, API_HASH, or BOT_TOKEN.")

# Initialize Pyrogram Bot
bot = Client("bulk_thumbnail_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Flask app for web hosting (keep the bot alive)
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "🤖 Bot is running!"

# Directory for storing user thumbnails
THUMB_DIR = "thumbnails"
os.makedirs(THUMB_DIR, exist_ok=True)

# ✅ Set Thumbnail Command
@bot.on_message(filters.command("set_thumb") & filters.photo)
async def set_thumbnail(client, message):
    file_path = os.path.join(THUMB_DIR, f"{message.from_user.id}.jpg")
    await client.download_media(message.photo, file_name=file_path)
    await message.reply_text("✅ Thumbnail saved successfully!")

# ✅ File Rename & Thumbnail Change
@bot.on_message(filters.document)
async def change_thumbnail(client, message):
    thumb_path = os.path.join(THUMB_DIR, f"{message.from_user.id}.jpg")

    # Check if thumbnail exists
    if not os.path.exists(thumb_path):
        await message.reply_text("⚠️ No thumbnail found! Use /set_thumb to set one.")
        return

    # Check file size (max 2GB limit for normal users)
    file_size = message.document.file_size
    max_size = 2 * 1024 * 1024 * 1024  # 2GB

    if file_size > max_size:
        await message.reply_text("❌ File is too large (Max: 2GB).")
        return

    await message.reply_text("🔄 Processing file...")

    # Download the document
    file_path = await client.download_media(message)

    if not file_path:
        await message.reply_text("❌ Failed to download file.")
        return

    # Extract filename & clean it
    file_name, file_ext = os.path.splitext(message.document.file_name)

    # Remove anything inside brackets [ ]
    file_name = re.sub(r"\[.*?\]", "", file_name)

    # Remove any word starting with '@'
    file_name = re.sub(r"@\S+", "", file_name)

    # Trim extra spaces
    file_name = file_name.strip()

    # Ensure the filename starts with [@Animes2u]
    new_filename = f"{DEFAULT_KEYWORD}{file_name}{file_ext}"
    new_file_path = os.path.join(os.path.dirname(file_path), new_filename)

    # ✅ Rename the file before uploading to prevent duplicates
    os.rename(file_path, new_file_path)

    try:
        # Send renamed file with thumbnail
        await client.send_document(
            chat_id=message.chat.id,
            document=new_file_path,
            thumb=thumb_path,
            file_name=new_filename,
            caption=f"✅ Renamed: {new_filename}",
        )
        await message.reply_text("✅ Done! Here is your updated file.")

        # ✅ Delete temp file to free space
        os.remove(new_file_path)

    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# ✅ Start Command
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "👋 Hello! Send an image with /set_thumb to set a thumbnail, then send a file to rename & change its thumbnail."
    )

# Run Flask in a separate thread
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    print(f"🌍 Starting Flask on port {port}...")
    web_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    print("🤖 Bot is starting...")

    # Start Flask server
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Start Telegram Bot
    try:
        bot.start()
        print("✅ Bot is online.")
    except Exception as e:
        print(f"❌ Bot startup failed: {e}")

    # Keep bot running
    idle()

    print("🛑 Bot stopped.")
    bot.stop()
