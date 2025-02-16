import os
import yt_dlp
import openai
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# Set up your tokens
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

openai.api_key = OPENAI_API_KEY

# Function to get AI response
async def chat_with_ai(user_message):
    response = openai.ChatCompletion.create(
        model="gpt-4", messages=[{"role": "user", "content": user_message}]
    )
    return response["choices"][0]["message"]["content"]

# Start command
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    buttons = [
        InlineKeyboardButton("Download Video", callback_data="download_video"),
        InlineKeyboardButton("Download Playlist", callback_data="download_playlist"),
        InlineKeyboardButton("Chat with AI", callback_data="chat_ai")
    ]
    keyboard = InlineKeyboardMarkup(row_width=2).add(*buttons)
    await message.answer("Hello! I'm a smart AI bot. Choose an option:", reply_markup=keyboard)

# Handle AI chat
@dp.callback_query_handler(lambda c: c.data == "chat_ai")
async def ai_chat_prompt(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Send me any message, and I'll reply with AI.")

@dp.message_handler()
async def ai_chat(message: types.Message):
    ai_response = await chat_with_ai(message.text)
    await message.reply(ai_response)

# Handle video download request
@dp.callback_query_handler(lambda c: c.data == "download_video")
async def ask_for_url(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Send me the YouTube video URL.")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def fetch_video_qualities(message: types.Message):
    url = message.text
    available_qualities = get_available_qualities(url)

    if not available_qualities:
        await message.reply("Could not retrieve video qualities. Try another video.")
        return

    buttons = [InlineKeyboardButton(q, callback_data=f"quality_{q}_{url}") for q in available_qualities]
    keyboard = InlineKeyboardMarkup(row_width=2).add(*buttons)
    await message.reply("Choose a quality:", reply_markup=keyboard)

# Get available video qualities dynamically
def get_available_qualities(url):
    ydl_opts = {"quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            formats = info.get("formats", [])
            qualities = set()
            for fmt in formats:
                if "height" in fmt and fmt["height"]:
                    qualities.add(f"{fmt['height']}p")
                elif fmt.get("acodec") != "none" and fmt.get("vcodec") == "none":
                    qualities.add("Audio Only")
            return sorted(qualities, key=lambda x: int(x.replace("p", "")) if "p" in x else 0, reverse=True)
        except Exception:
            return []

# Handle quality selection and download
@dp.callback_query_handler(lambda c: c.data.startswith("quality_"))
async def download_video(callback_query: types.CallbackQuery):
    _, quality, url = callback_query.data.split("_", 2)

    ydl_opts = {
        "format": f"bestvideo[height={quality[:-1]}]+bestaudio/best" if "p" in quality else "bestaudio",
        "outtmpl": f"{callback_query.from_user.id}.%(ext)s",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}] if quality == "Audio Only" else []
    }

    await bot.send_message(callback_query.from_user.id, f"Downloading {quality} version...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    file_name = next((f for f in os.listdir() if f.startswith(str(callback_query.from_user.id))), None)

    if file_name:
        await bot.send_document(callback_query.from_user.id, open(file_name, "rb"))
        os.remove(file_name)  # Clean up after sending
    else:
        await bot.send_message(callback_query.from_user.id, "Failed to download.")

# Run bot
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
