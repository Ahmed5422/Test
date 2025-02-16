import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL

# Telegram Bot Token
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Start Command
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Download Video", callback_data="download_video"),
        InlineKeyboardButton("Download Playlist", callback_data="download_playlist")
    )
    await message.reply("Welcome! Choose an option:", reply_markup=keyboard)

# Handle Button Clicks
@dp.callback_query_handler(lambda c: c.data in ["download_video", "download_playlist"])
async def handle_buttons(callback_query: types.CallbackQuery):
    action = "video" if callback_query.data == "download_video" else "playlist"
    await bot.send_message(callback_query.from_user.id, f"Send the {action} URL:")

# Handle YouTube Links
@dp.message_handler(lambda message: "youtube.com" in message.text or "youtu.be" in message.text)
async def process_video(message: types.Message):
    url = message.text
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Video", callback_data=f"quality_{url}_video"),
        InlineKeyboardButton("Audio", callback_data=f"quality_{url}_audio")
    )
    await message.reply("Choose format:", reply_markup=keyboard)

# Quality Selection
@dp.callback_query_handler(lambda c: c.data.startswith("quality_"))
async def choose_quality(callback_query: types.CallbackQuery):
    data = callback_query.data.split("_")
    url = data[1]
    format_type = data[2]

    ydl_opts = {
        'format': 'bestaudio/best' if format_type == "audio" else 'best',
        'outtmpl': f'{callback_query.from_user.id}.%(ext)s'
    }

    await bot.send_message(callback_query.from_user.id, "Downloading...")

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    await bot.send_document(callback_query.from_user.id, open(filename, "rb"))
    os.remove(filename)

# Run Bot
if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp)
