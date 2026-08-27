import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from gtts import gTTS
import yt_dlp

# Твой токен вставлен!
BOT_TOKEN = "8963766433:AAFX8f3AW0IuHq_BDBVPhgU4U3wcMAhjGPA"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

os.makedirs("downloads", exist_ok=True)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "🚀 **Привет! Я твой медиа-помощник.**\n\n"
        "🎬 **Что я умею:**\n"
        "1. Отправь ссылку (TikTok, Reels, Shorts) — скачаю без лого!\n"
        "2. Отправь любое видео — сделаю из него кружочек!\n"
        "3. Напиши `/say Текст` — я озвучу его в голосовое!"
    )

@dp.message(F.text.startswith("http://") | F.text.startswith("https://"))
async def download_video_handler(message: types.Message):
    url = message.text.strip()
    status_msg = await message.answer("⏳ Скачиваю видео, подожди немного...")
    output_path = f"downloads/{message.from_user.id}_video.mp4"
    ydl_opts = {'format': 'mp4', 'outtmpl': output_path, 'quiet': True}
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
        if os.path.exists(output_path):
            await message.answer_video(FSInputFile(output_path), caption="✅ Готово! Твое видео без логотипа.")
            os.remove(output_path)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Не удалось скачать видео по этой ссылке.")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка скачивания: {str(e)}")

@dp.message(F.video | F.document)
async def convert_to_note_handler(message: types.Message):
    status_msg = await message.answer("🔄 Делаю кружочек из видео...")
    file_id = message.video.file_id if message.video else message.document.file_id
    file = await bot.get_file(file_id)
    input_file = f"downloads/{message.from_user.id}_input.mp4"
    output_note = f"downloads/{message.from_user.id}_note.mp4"
    await bot.download_file(file.file_path, input_file)
    
    ffmpeg_cmd = f'ffmpeg -y -i {input_file} -vf "crop=ih:ih,scale=640:640" -c:v libx264 -crf 26 -preset ultrafast -c:a aac {output_note}'
    process = await asyncio.create_subprocess_shell(ffmpeg_cmd)
    await process.communicate()

    if os.path.exists(output_note):
        await message.answer_video_note(FSInputFile(output_note))
        await status_msg.delete()
        os.remove(input_file)
        os.remove(output_note)
    else:
        await status_msg.edit_text("❌ Не удалось сделать кружочек.")

@dp.message(F.text.startswith("/say"))
async def text_to_speech_handler(message: types.Message):
    text = message.text.replace("/say", "").strip()
    if not text:
        return await message.answer("⚠️ Напиши текст после команды, например: `/say Привет как дела`")
    output_audio = f"downloads/{message.from_user.id}_audio.ogg"
    gTTS(text=text, lang='ru').save(output_audio)
    await message.answer_voice(FSInputFile(output_audio))
    os.remove(output_audio)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
