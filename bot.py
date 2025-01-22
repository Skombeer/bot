import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from yt_dlp import YoutubeDL
from config import BOT_TOKEN
from config import PROXY

bot = Bot(token=BOT_TOKEN, timeout=10)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="/start")]],
    resize_keyboard=True
)
empty_keyboard = ReplyKeyboardMarkup(
    keyboard=[],
    resize_keyboard=True
)

def search_music(query):
    ydl_opts = {
        'quiet': True,
        'default_search': 'ytsearch3',
        'extract_flat': True,
        'proxy': PROXY
    }
    with YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(query, download=False)
        return result['entries'] if 'entries' in result else []

def download_audio(url: str) -> str:
    """
    Скачивает аудио с YouTube и возвращает путь к скачанному файлу.
    """
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True, 
        'proxy': PROXY
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return os.path.join(output_dir, f"{info['title']}.mp3")

@dp.message(F.text == "/start")
async def send_welcome(message: types.Message):
    await message.reply(
        "Привет! Напиши название песни, и я найду её для тебя.", 
        reply_markup=empty_keyboard
    )

@dp.message(F.text)
async def search_and_send_music(message: types.Message):
    query = message.text.strip()
    if query.startswith("/"):
        return

    await message.reply(f"Ищу '{query}'...")

    search_results = search_music(query)
    
    if search_results:
        for result in search_results:
            title = result['title']
            url = result['url']
            
            try:
                audio_path = download_audio(url)
                await message.answer(f"Нашел: {title}\nСкачиваю аудио...")

                with open(audio_path, 'rb') as audio:
                    await message.answer_audio(audio, caption=title)

                os.remove(audio_path)

            except Exception as e:
                await message.reply(f"Не удалось скачать аудио: {e}")
    else:
        await message.reply("Не удалось найти музыку по вашему запросу.")

@dp.message()
async def handle_first_message(message: types.Message):
    await message.reply("Нажмите /start, чтобы начать.", reply_markup=keyboard)

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())