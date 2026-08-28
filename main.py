import os
import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
import aiohttp
import yt_dlp
import static_ffmpeg

static_ffmpeg.add_paths()

# Жестко вшитые ключи
TOKEN = os.getenv("BOT_TOKEN", "8765852488:AAErO2_3gbQCR8UG7AncX64p2d3W3z5W0Tg")
ELEVEN_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_053e9cf42e316b2532d4ed3c2049d29622ec80f81d7fe01d")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

users_db = set()
stats = {
    "music": 0,
    "tts": 0,
    "video": 0,
    "note": 0,
    "sticker": 0
}
user_langs = {}
pending_links = {}

TEXTS = {
    "ru": {
        "start": "🚀 **Привет! Я твой универсальный медиа-помощник.**\n\n✨ **Мои возможности:**\n1. 📩 **Скачивание по ссылке** — отправь ссылку и скачай Видео или MP3.\n2. 🔍 **Поиск музыки** — напиши `/music Название`\n3. 🔄 **Видео ↔ Кружочек** — отправь видео или кружочек.\n4. 🖼 **Фото в стикер** — отправь картинку.\n5. 🗣 **ИИ Озвучка текста** — напиши `/say Текст`",
        "lang_select": "🌐 Выберите язык / Tilingizni tanlang / Select language:",
        "lang_set": "✅ Язык успешно изменен на Русский!",
        "stats": "📊 **Статистика бота:**\n\n👥 Пользователи: {users}\n🔍 Найдено песен: {music}\n🗣 Озвучено ElevenLabs: {tts}\n🎬 Скачано видео: {video}\n🔄 Кружочки: {note}\n🖼 Стикеры: {sticker}",
        "say_prompt": "⚠️ Напишите текст после команды: `/say Привет`",
        "music_prompt": "⚠️ Напишите название песни: `/music Miyagi`",
        "music_err": "❌ Ошибка при поиске музыки.",
        "dl_prompt": "Что скачиваем?",
        "dl_start": "⏳ Загружаю...",
        "dl_err": "❌ Не удалось скачать по этой ссылке."
    },
    "uz": {
        "start": "🚀 **Salom! Men sizning universal media yordamchingizman.**\n\n✨ **Imkoniyatlarim:**\n1. 📩 **Havola orqali yuklash** — Video yoki MP3 yuklab oling.\n2. 🔍 **Musiqa qidirish** — `/music Nomi` deb yozing.\n3. 🔄 **Video ↔ Dumaloq video** — video yoki dumaloq video yuboring.\n4. 🖼 **Rasm stickerga** — rasm yuboring.\n5. 🗣 **AI Ovoz berish** — `/say Matn` deb yozing.",
        "lang_select": "🌐 Выберите язык / Tilingizni tanlang / Select language:",
        "lang_set": "✅ Tilingiz O'zbekchaga o'zgartirildi!",
        "stats": "📊 **Bot statistikasi:**\n\n👥 Foydalanuvchilar: {users}\n🔍 Topilgan qo'shiqlar: {music}\n🗣 AI Ovozlar: {tts}\n🎬 Yuklangan videolar: {video}\n🔄 Dumaloq videolar: {note}\n🖼 Stikerlar: {sticker}",
        "say_prompt": "⚠️ Buyruqdan so'ng matn yozing: `/say Salom`",
        "music_prompt": "⚠️ Musiqa nomini yozing: `/music Miyagi`",
        "music_err": "❌ Musiqa qidirishda xatolik.",
        "dl_prompt": "Nima yuklab olamiz?",
        "dl_start": "⏳ Yuklanmoqda...",
        "dl_err": "❌ Yuklab bo'lmadi."
    },
    "en": {
        "start": "🚀 **Hello! I am your universal media assistant.**\n\n✨ **Features:**\n1. 📩 **Download by link** — send link to get Video or MP3.\n2. 🔍 **Music search** — type `/music Name`.\n3. 🔄 **Video ↔ Video Note** — send video or video note.\n4. 🖼 **Photo to Sticker** — send an image.\n5. 🗣 **AI Text-to-Speech** — type `/say Text`.",
        "lang_select": "🌐 Выберите язык / Tilingizni tanlang / Select language:",
        "lang_set": "✅ Language changed to English!",
        "stats": "📊 **Bot Statistics:**\n\n👥 Users: {users}\n🔍 Music found: {music}\n🗣 TTS Generated: {tts}\n🎬 Videos downloaded: {video}\n🔄 Video notes: {note}\n🖼 Stickers: {sticker}",
        "say_prompt": "⚠️ Write text after command: `/say Hello`",
        "music_prompt": "⚠️ Write song name: `/music Miyagi`",
        "music_err": "❌ Search error.",
        "dl_prompt": "What to download?",
        "dl_start": "⏳ Downloading...",
        "dl_err": "❌ Failed to download."
    }
}

def get_txt(user_id, key):
    lang = user_langs.get(user_id, "ru")
    return TEXTS[lang].get(key, TEXTS["ru"][key])

@dp.message(CommandStart())
async def cmd_start(msg: types.Message):
    users_db.add(msg.from_user.id)
    await msg.answer(get_txt(msg.from_user.id, "start"), parse_mode="Markdown")

@dp.message(Command("lang"))
async def cmd_lang(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    await msg.answer(get_txt(msg.from_user.id, "lang_select"), reply_markup=kb)

@dp.callback_query(F.data.startswith("lang_"))
async def set_language(cb: types.CallbackQuery):
    lang_code = cb.data.split("_")[1]
    user_langs[cb.from_user.id] = lang_code
    await cb.message.edit_text(get_txt(cb.from_user.id, "lang_set"))
    await cb.answer()

@dp.message(Command("stats"))
async def cmd_stats(msg: types.Message):
    text = get_txt(msg.from_user.id, "stats").format(
        users=len(users_db),
        music=stats["music"],
        tts=stats["tts"],
        video=stats["video"],
        note=stats["note"],
        sticker=stats["sticker"]
    )
    await msg.answer(text, parse_mode="Markdown")

@dp.message(Command("say"))
async def cmd_say(msg: types.Message):
    users_db.add(msg.from_user.id)
    text = msg.text.replace("/say", "").strip()
    if not text:
        return await msg.answer(get_txt(msg.from_user.id, "say_prompt"), parse_mode="Markdown")
    
    voice_id = "21m00Tcm4TlvDq8ikWAM"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_KEY
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    audio_bytes = await resp.read()
                    file_path = f"tts_{msg.from_user.id}.mp3"
                    with open(file_path, "wb") as f:
                        f.write(audio_bytes)
                    
                    await msg.answer_voice(voice=FSInputFile(file_path))
                    stats["tts"] += 1
                    os.remove(file_path)
                else:
                    err_body = await resp.text()
                    await msg.answer(f"❌ ElevenLabs Error ({resp.status}): {err_body}")
    except Exception as e:
        await msg.answer(f"❌ Error: {str(e)}")

@dp.message(Command("music"))
async def cmd_music(msg: types.Message):
    users_db.add(msg.from_user.id)
    query = msg.text.replace("/music", "").strip()
    if not query:
        return await msg.answer(get_txt(msg.from_user.id, "music_prompt"), parse_mode="Markdown")

    status_msg = await msg.answer("🔎 Ищу песню...")
    out_file = f"music_{msg.from_user.id}.mp3"

    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1:',
        'outtmpl': f"music_{msg.from_user.id}.%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([query]))
        await msg.answer_audio(audio=FSInputFile(out_file), title=query)
        stats["music"] += 1
        if os.path.exists(out_file):
            os.remove(out_file)
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(get_txt(msg.from_user.id, "music_err"))

# Обработка ссылки с выбором (Видео / Аудио)
@dp.message(F.text.regexp(r'https?://[^\s]+'))
async def handle_links_prompt(msg: types.Message):
    users_db.add(msg.from_user.id)
    pending_links[msg.from_user.id] = msg.text.strip()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 Видео", callback_data="dl_video"),
            InlineKeyboardButton(text="🎵 Аудио (MP3)", callback_data="dl_audio")
        ]
    ])
    await msg.answer(get_txt(msg.from_user.id, "dl_prompt"), reply_markup=kb)

@dp.callback_query(F.data.startswith("dl_"))
async def process_download(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    url = pending_links.get(user_id)
    if not url:
        return await cb.answer("Ссылка не найдена.", show_alert=True)
    
    mode = cb.data.split("_")[1]
    await cb.message.edit_text(get_txt(user_id, "dl_start"))

    if mode == "video":
        out_file = f"video_{user_id}.mp4"
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': out_file,
            'quiet': True
        }
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
            if os.path.exists(out_file):
                await cb.message.answer_video(video=FSInputFile(out_file))
                stats["video"] += 1
                os.remove(out_file)
                await cb.message.delete()
            else:
                await cb.message.edit_text(get_txt(user_id, "dl_err"))
        except Exception:
            await cb.message.edit_text(get_txt(user_id, "dl_err"))

    elif mode == "audio":
        out_file = f"audio_{user_id}.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"audio_{user_id}.%(ext)s",
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
            if os.path.exists(out_file):
                await cb.message.answer_audio(audio=FSInputFile(out_file))
                stats["music"] += 1
                os.remove(out_file)
                await cb.message.delete()
            else:
                await cb.message.edit_text(get_txt(user_id, "dl_err"))
        except Exception:
            await cb.message.edit_text(get_txt(user_id, "dl_err"))

# 1. Обычное видео ➔ Кружочек
@dp.message(F.video)
async def handle_video_to_note(msg: types.Message):
    users_db.add(msg.from_user.id)
    status_msg = await msg.answer("⏳ Создаю кружочек...")
    
    in_path = f"in_{msg.from_user.id}.mp4"
    out_path = f"out_{msg.from_user.id}.mp4"

    await bot.download(msg.video, destination=in_path)

    cmd = f'ffmpeg -y -i "{in_path}" -vf "crop=min(iw\\,ih):min(iw\\,ih),scale=480:480:force_original_aspect_ratio=decrease" -c:v libx264 -crf 26 -preset ultrafast -c:a aac -b:a 128k "{out_path}"'
    
    proc = await asyncio.create_subprocess_shell(cmd)
    await proc.communicate()

    if os.path.exists(out_path):
        await msg.answer_video_note(video_note=FSInputFile(out_path))
        stats["note"] += 1
        os.remove(out_path)
    else:
        await msg.answer("❌ Не удалось обработать видео.")

    if os.path.exists(in_path):
        os.remove(in_path)
    await status_msg.delete()

# 2. Кружочек ➔ Обычное видео
@dp.message(F.video_note)
async def handle_note_to_video(msg: types.Message):
    users_db.add(msg.from_user.id)
    status_msg = await msg.answer("⏳ Преобразую в обычное видео...")
    
    in_path = f"note_in_{msg.from_user.id}.mp4"
    await bot.download(msg.video_note, destination=in_path)

    if os.path.exists(in_path):
        await msg.answer_video(video=FSInputFile(in_path))
        os.remove(in_path)
        await status_msg.delete()
    else:
        await status_msg.edit_text("❌ Ошибка при конвертации кружочка.")

@dp.message(F.photo)
async def handle_photo_to_sticker(msg: types.Message):
    users_db.add(msg.from_user.id)
    photo = msg.photo[-1]
    file_path = f"sticker_{msg.from_user.id}.webp"
    await bot.download(photo, destination=file_path)
    await msg.answer_sticker(sticker=FSInputFile(file_path))
    stats["sticker"] += 1
    os.remove(file_path)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
