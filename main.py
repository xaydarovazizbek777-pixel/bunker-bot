import os
import json
import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
import aiohttp
import yt_dlp
import static_ffmpeg

# Автоматическая настройка пути к FFmpeg
static_ffmpeg.add_paths()

TOKEN = os.getenv("BOT_TOKEN", "8765852488:AAErO2_3gbQCR8UG7AncX64p2d3W3z5W0Tg")
ELEVEN_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_053e9cf42e316b2532d4ed3c2049d29622ec80f81d7fe01d")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

DB_FILE = "database.json"

# === СОХРАНЕНИЕ И ЗАГРУЗКА БАЗЫ ДАННЫХ ===
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "users": [],
        "user_langs": {},
        "stats": {"music": 0, "tts": 0, "video": 0, "note": 0, "sticker": 0}
    }

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

db = load_db()
pending_links = {}

def register_user(user_id):
    user_str = str(user_id)
    if user_str not in db["users"]:
        db["users"].append(user_str)
        save_db()

def get_lang(user_id):
    return db["user_langs"].get(str(user_id), "ru")

# === МУЛЬТИЯЗЫЧНЫЕ ТЕКСТЫ ===
TEXTS = {
    "ru": {
        "start": "🚀 **Привет! Я твой универсальный медиа-помощник.**\n\n✨ **Мои возможности:**\n1. 📩 **Скачивание по ссылке** — отправь ссылку (TikTok, Reels, Shorts) и выбери Видео или MP3.\n2. 🔍 **Поиск музыки** — напиши `/music Название песни`\n3. 🔄 **Видео ↔ Кружочек** — отправь обычное видео или кружочек.\n4. 🖼 **Фото в стикер** — отправь любое фото.\n5. 🗣 **ИИ-Озвучка текста** — напиши `/say Текст`\n6. 🌐 **Смена языка** — команда `/lang`",
        "lang_select": "🌐 Выберите язык / Tilingizni tanlang / Select language:",
        "lang_set": "✅ Язык успешно изменен на Русский!",
        "stats": "📊 **Статистика бота:**\n\n👥 Всего пользователей: {users}\n🔍 Найдено песен: {music}\n🗣 Озвучек ElevenLabs: {tts}\n🎬 Скачано видео: {video}\n🔄 Кружочков сделано: {note}\n🖼 Стикеров сделано: {sticker}",
        "say_prompt": "⚠️ Напишите текст после команды. Пример: `/say Привет, как дела?`",
        "music_prompt": "⚠️ Напишите название песни. Пример: `/music Miyagi` или `/music Janob Rasul`",
        "music_search": "🔎 Ищу песню, подождите...",
        "music_err": "❌ Не удалось найти или скачать эту песню.",
        "dl_prompt": "Что именно скачиваем?",
        "dl_start": "⏳ Скачиваю файл...",
        "dl_err": "❌ Ошибка при скачивании по этой ссылке."
    },
    "uz": {
        "start": "🚀 **Salom! Men sizning universal media yordamchingizman.**\n\n✨ **Imkoniyatlarim:**\n1. 📩 **Havola orqali yuklash** — TikTok, Reels yoki Shorts havolasini yuboring.\n2. 🔍 **Musiqa qidirish** — `/music Qo'shiq nomi` deb yozing.\n3. 🔄 **Video ↔ Dumaloq video** — video yoki dumaloq video yuboring.\n4. 🖼 **Rasm stickerga** — rasm yuboring.\n5. 🗣 **AI Ovoz berish** — `/say Matn` deb yozing.\n6. 🌐 **Tilni o'zgartirish** — `/lang` buyrug'i",
        "lang_select": "🌐 Выберите язык / Tilingizni tanlang / Select language:",
        "lang_set": "✅ Tilingiz O'zbekchaga o'zgartirildi!",
        "stats": "📊 **Bot statistikasi:**\n\n👥 Jami foydalanuvchilar: {users}\n🔍 Qidirilgan qo'shiqlar: {music}\n🗣 AI Ovozlar: {tts}\n🎬 Yuklangan videolar: {video}\n🔄 Dumaloq videolar: {note}\n🖼 Stikerlar: {sticker}",
        "say_prompt": "⚠️ Buyruqdan so'ng matn yozing. Masalan: `/say Salom, qalaysiz?`",
        "music_prompt": "⚠️ Qo'shiq nomini yozing. Masalan: `/music Miyagi` yoki `/music Rayhon`",
        "music_search": "🔎 Qo'shiq qidirilmoqda...",
        "music_err": "❌ Musiqa topilmadi yoki yuklab bo'lmadi.",
        "dl_prompt": "Nimani yuklab olamiz?",
        "dl_start": "⏳ Yuklanmoqda...",
        "dl_err": "❌ Ushbu havoladan yuklab bo'lmadi."
    },
    "en": {
        "start": "🚀 **Hello! I am your universal media assistant.**\n\n✨ **Features:**\n1. 📩 **Download by link** — send a link (TikTok, Reels, Shorts) and choose Video or MP3.\n2. 🔍 **Music Search** — type `/music Song title`\n3. 🔄 **Video ↔ Video Note** — send video or video note.\n4. 🖼 **Photo to Sticker** — send any image.\n5. 🗣 **AI Text-to-Speech** — type `/say Text`\n6. 🌐 **Change language** — type `/lang`",
        "lang_select": "🌐 Выберите язык / Tilingizni tanlang / Select language:",
        "lang_set": "✅ Language changed to English!",
        "stats": "📊 **Bot Statistics:**\n\n👥 Total Users: {users}\n🔍 Music Found: {music}\n🗣 TTS Generated: {tts}\n🎬 Videos Downloaded: {video}\n🔄 Video Notes: {note}\n🖼 Stickers Created: {sticker}",
        "say_prompt": "⚠️ Write text after command. Example: `/say Hello world`",
        "music_prompt": "⚠️ Write song name. Example: `/music Imagine Dragons`",
        "music_search": "🔎 Searching for music...",
        "music_err": "❌ Could not find or download this song.",
        "dl_prompt": "What do you want to download?",
        "dl_start": "⏳ Downloading...",
        "dl_err": "❌ Failed to download from this link."
    }
}

def get_txt(user_id, key):
    lang = get_lang(user_id)
    return TEXTS[lang].get(key, TEXTS["ru"][key])

# === КОМАНДЫ ===
@dp.message(CommandStart())
async def cmd_start(msg: types.Message):
    register_user(msg.from_user.id)
    await msg.answer(get_txt(msg.from_user.id, "start"), parse_mode="Markdown")

@dp.message(Command("lang"))
async def cmd_lang(msg: types.Message):
    register_user(msg.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    await msg.answer(get_txt(msg.from_user.id, "lang_select"), reply_markup=kb)

@dp.callback_query(F.data.startswith("lang_"))
async def set_language(cb: types.CallbackQuery):
    lang_code = cb.data.split("_")[1]
    db["user_langs"][str(cb.from_user.id)] = lang_code
    save_db()
    await cb.message.edit_text(get_txt(cb.from_user.id, "lang_set"))
    await cb.answer()

@dp.message(Command("stats"))
async def cmd_stats(msg: types.Message):
    register_user(msg.from_user.id)
    s = db["stats"]
    text = get_txt(msg.from_user.id, "stats").format(
        users=len(db["users"]),
        music=s["music"],
        tts=s["tts"],
        video=s["video"],
        note=s["note"],
        sticker=s["sticker"]
    )
    await msg.answer(text, parse_mode="Markdown")

@dp.message(Command("say"))
async def cmd_say(msg: types.Message):
    register_user(msg.from_user.id)
    text = msg.text.replace("/say", "").strip()
    if not text:
        return await msg.answer(get_txt(msg.from_user.id, "say_prompt"), parse_mode="Markdown")
    
    status_msg = await msg.answer("🗣 Озвучиваю...")
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
            async with session.post(url, json=payload, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    audio_bytes = await resp.read()
                    file_path = f"tts_{msg.from_user.id}.mp3"
                    with open(file_path, "wb") as f:
                        f.write(audio_bytes)
                    
                    await msg.answer_voice(voice=FSInputFile(file_path))
                    db["stats"]["tts"] += 1
                    save_db()
                    os.remove(file_path)
                    await status_msg.delete()
                else:
                    err_body = await resp.text()
                    await status_msg.edit_text(f"❌ Ошибка ElevenLabs ({resp.status}). Проверьте токен или лимиты.")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка при запросе: {str(e)}")

@dp.message(Command("music"))
async def cmd_music(msg: types.Message):
    register_user(msg.from_user.id)
    query = msg.text.replace("/music", "").strip()
    if not query:
        return await msg.answer(get_txt(msg.from_user.id, "music_prompt"), parse_mode="Markdown")

    status_msg = await msg.answer(get_txt(msg.from_user.id, "music_search"))
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
        'quiet': True,
        'socket_timeout': 10,
        'nocheckcertificate': True
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([query]))
        if os.path.exists(out_file):
            await msg.answer_audio(audio=FSInputFile(out_file), title=query)
            db["stats"]["music"] += 1
            save_db()
            os.remove(out_file)
            await status_msg.delete()
        else:
            await status_msg.edit_text(get_txt(msg.from_user.id, "music_err"))
    except Exception:
        await status_msg.edit_text(get_txt(msg.from_user.id, "music_err"))

# === СКАЧИВАНИЕ ПО ССЫЛКЕ ===
@dp.message(F.text.regexp(r'https?://[^\s]+'))
async def handle_links_prompt(msg: types.Message):
    register_user(msg.from_user.id)
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
            'quiet': True,
            'socket_timeout': 15
        }
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
            if os.path.exists(out_file):
                await cb.message.answer_video(video=FSInputFile(out_file))
                db["stats"]["video"] += 1
                save_db()
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
            'quiet': True,
            'socket_timeout': 15
        }
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
            if os.path.exists(out_file):
                await cb.message.answer_audio(audio=FSInputFile(out_file))
                db["stats"]["music"] += 1
                save_db()
                os.remove(out_file)
                await cb.message.delete()
            else:
                await cb.message.edit_text(get_txt(user_id, "dl_err"))
        except Exception:
            await cb.message.edit_text(get_txt(user_id, "dl_err"))

# === КОНВЕРТАЦИЯ ВИДЕО ↔ КРУЖОЧЕК ===
@dp.message(F.video)
async def handle_video_to_note(msg: types.Message):
    register_user(msg.from_user.id)
    status_msg = await msg.answer("⏳ Создаю кружочек...")
    
    in_path = f"in_{msg.from_user.id}.mp4"
    out_path = f"out_{msg.from_user.id}.mp4"

    await bot.download(msg.video, destination=in_path)

    cmd = f'ffmpeg -y -i "{in_path}" -vf "crop=min(iw\\,ih):min(iw\\,ih),scale=480:480:force_original_aspect_ratio=decrease" -c:v libx264 -crf 26 -preset ultrafast -c:a aac -b:a 128k "{out_path}"'
    
    proc = await asyncio.create_subprocess_shell(cmd)
    await proc.communicate()

    if os.path.exists(out_path):
        await msg.answer_video_note(video_note=FSInputFile(out_path))
        db["stats"]["note"] += 1
        save_db()
        os.remove(out_path)
    else:
        await msg.answer("❌ Ошибка обработки видео.")

    if os.path.exists(in_path):
        os.remove(in_path)
    await status_msg.delete()

@dp.message(F.video_note)
async def handle_note_to_video(msg: types.Message):
    register_user(msg.from_user.id)
    status_msg = await msg.answer("⏳ Преобразую кружочек в обычное видео...")
    
    in_path = f"note_in_{msg.from_user.id}.mp4"
    await bot.download(msg.video_note, destination=in_path)

    if os.path.exists(in_path):
        await msg.answer_video(video=FSInputFile(in_path))
        os.remove(in_path)
        await status_msg.delete()
    else:
        await status_msg.edit_text("❌ Ошибка при обратной конвертации.")

# === ФОТО В СТИКЕР ===
@dp.message(F.photo)
async def handle_photo_to_sticker(msg: types.Message):
    register_user(msg.from_user.id)
    photo = msg.photo[-1]
    file_path = f"sticker_{msg.from_user.id}.webp"
    await bot.download(photo, destination=file_path)
    await msg.answer_sticker(sticker=FSInputFile(file_path))
    db["stats"]["sticker"] += 1
    save_db()
    os.remove(file_path)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
