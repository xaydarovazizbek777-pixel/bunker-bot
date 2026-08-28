import os
import json
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from gtts import gTTS
import yt_dlp
import static_ffmpeg

static_ffmpeg.add_paths()

TOKEN = os.getenv("BOT_TOKEN", "8765852488:AAErO2_3gbQCR8UG7AncX64p2d3W3z5W0Tg")
ADMIN_ID = 5435444673

logging.basicConfig(level=logging.INFO)

DB_FILE = "database.json"

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

TEXTS = {
    "ru": {
        "start": "🚀 **Привет! Я твой универсальный медиа-помощник.**\n\n✨ **Мои возможности:**\n1. 📩 **Скачивание по ссылке** — отправь ссылку (TikTok, Reels, Shorts) и выбери Видео или MP3.\n2. 🔍 **Поиск музыки** — напиши `/music Название`\n3. 🔄 **Видео ↔ Кружочек** — отправь видео или кружочек.\n4. 🖼 **Фото в стикер** — отправь фото.\n5. 🗣 **Озвучка текста** — напиши `/say Текст`\n6. 🌐 **Смена языка** — команда `/lang`",
        "lang_select": "🌐 Выберите язык / Tilingizni tanlang / Select language:",
        "lang_set": "✅ Язык успешно изменен на Русский!",
        "stats": "📊 **Статистика бота:**\n\n👥 Всего пользователей: {users}\n🔍 Найдено песен: {music}\n🗣 Озвучено текстов: {tts}\n🎬 Скачано видео: {video}\n🔄 Кружочков сделано: {note}\n🖼 Стикеров сделано: {sticker}",
        "no_access": "⛔ У вас нет доступа к этой команде!",
        "say_prompt": "⚠️ Напишите текст после команды: `/say Привет, как дела?`",
        "music_prompt": "⚠️ Напишите название песни: `/music Miyagi`",
        "music_search": "🔎 Ищу песню, подождите...",
        "music_err": "❌ Не удалось найти или скачать эту песню.",
        "dl_prompt": "Что именно скачиваем?",
        "dl_start": "⏳ Скачиваю файл...",
        "dl_err": "❌ Ошибка при скачивании по этой ссылке."
    },
    "uz": {
        "start": "🚀 **Salom! Men sizning universal media yordamchingizman.**\n\n✨ **Imkoniyatlarim:**\n1. 📩 **Havola orqali yuklash** — TikTok, Reels yoki Shorts havolasini yuboring.\n2. 🔍 **Musiqa qidirish** — `/music Qo'shiq nomi` deb yozing.\n3. 🔄 **Video ↔ Dumaloq video** — video yoki dumaloq video yuboring.\n4. 🖼 **Rasm stickerga** — rasm yuboring.\n5. 🗣 **Ovoz berish** — `/say Matn` deb yozing.\n6. 🌐 **Tilni o'zgartirish** — `/lang` buyrug'i",
        "lang_select": "🌐 Выберите язык / Tilingizni tanlang / Select language:",
        "lang_set": "✅ Tilingiz O'zbekchaga o'zgartirildi!",
        "stats": "📊 **Bot statistikasi:**\n\n👥 Jami foydalanuvchilar: {users}\n🔍 Qidirilgan qo'shiqlar: {music}\n🗣 Ovoz berilgan: {tts}\n🎬 Yuklangan videolar: {video}\n🔄 Dumaloq videolar: {note}\n🖼 Stikerlar: {sticker}",
        "no_access": "⛔ Sizda ushbu buyruqdan foydalanish huquqi yo'q!",
        "say_prompt": "⚠️ Buyruqdan so'ng matn yozing: `/say Salom, qalaysiz?`",
        "music_prompt": "⚠️ Qo'shiq nomini yozing: `/music Miyagi`",
        "music_search": "🔎 Qo'shiq qidirilmoqda...",
        "music_err": "❌ Musiqa topilmadi yoki yuklab bo'lmadi.",
        "dl_prompt": "Nimani yuklab olamiz?",
        "dl_start": "⏳ Yuklanmoqda...",
        "dl_err": "❌ Ushbu havoladan yuklab bo'lmadi."
    },
    "en": {
        "start": "🚀 **Hello! I am your universal media assistant.**\n\n✨ **Features:**\n1. 📩 **Download by link** — send a link and choose Video or MP3.\n2. 🔍 **Music Search** — type `/music Song title`\n3. 🔄 **Video ↔ Video Note** — send video or video note.\n4. 🖼 **Photo to Sticker** — send photo.\n5. 🗣 **Text-to-Speech** — type `/say Text`\n6. 🌐 **Change language** — type `/lang`",
        "lang_select": "🌐 Выберите язык / Tilingizni tanlang / Select language:",
        "lang_set": "✅ Language changed to English!",
        "stats": "📊 **Bot Statistics:**\n\n👥 Total Users: {users}\n🔍 Music Found: {music}\n🗣 TTS Generated: {tts}\n🎬 Videos Downloaded: {video}\n🔄 Video Notes: {note}\n🖼 Stickers Created: {sticker}",
        "no_access": "⛔ Access denied!",
        "say_prompt": "⚠️ Write text after command: `/say Hello world`",
        "music_prompt": "⚠️ Write song name: `/music Imagine Dragons`",
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

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    await update.message.reply_text(get_txt(user_id, "start"), parse_mode="Markdown")

async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ])
    await update.message.reply_text(get_txt(user_id, "lang_select"), reply_markup=kb)

async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = query.data.split("_")[1]
    db["user_langs"][str(query.from_user.id)] = lang_code
    save_db()
    await query.edit_message_text(get_txt(query.from_user.id, "lang_set"))

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    
    if user_id != ADMIN_ID:
        return await update.message.reply_text(get_txt(user_id, "no_access"))
        
    s = db["stats"]
    text = get_txt(user_id, "stats").format(
        users=len(db["users"]),
        music=s["music"],
        tts=s["tts"],
        video=s["video"],
        note=s["note"],
        sticker=s["sticker"]
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def say_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text(get_txt(user_id, "say_prompt"), parse_mode="Markdown")
    
    msg = await update.message.reply_text("🗣 Озвучиваю...")
    file_path = f"tts_{user_id}.mp3"
    try:
        user_lang = get_lang(user_id)
        tts = gTTS(text=text, lang=user_lang if user_lang in ['ru', 'en'] else 'ru')
        tts.save(file_path)

        with open(file_path, "rb") as f:
            await update.message.reply_voice(voice=f)
        
        db["stats"]["tts"] += 1
        save_db()
        os.remove(file_path)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка озвучки: {str(e)}")

async def music_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    query = " ".join(context.args)
    if not query:
        return await update.message.reply_text(get_txt(user_id, "music_prompt"), parse_mode="Markdown")

    msg = await update.message.reply_text(get_txt(user_id, "music_search"))
    out_file = f"music_{user_id}.mp3"

    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1:',
        'outtmpl': f"music_{user_id}.%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'socket_timeout': 15,
        'nocheckcertificate': True
    }

    try:
        ydl = yt_dlp.YoutubeDL(ydl_opts)
        ydl.download([query])
        if os.path.exists(out_file):
            with open(out_file, "rb") as f:
                await update.message.reply_audio(audio=f, title=query)
            db["stats"]["music"] += 1
            save_db()
            os.remove(out_file)
            await msg.delete()
        else:
            await msg.edit_text(get_txt(user_id, "music_err"))
    except Exception:
        await msg.edit_text(get_txt(user_id, "music_err"))

async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    pending_links[user_id] = update.message.text.strip()
    
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 Видео", callback_data="dl_video"),
            InlineKeyboardButton("🎵 Аудио (MP3)", callback_data="dl_audio")
        ]
    ])
    await update.message.reply_text(get_txt(user_id, "dl_prompt"), reply_markup=kb)

async def process_dl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    url = pending_links.get(user_id)
    
    if not url:
        return await query.edit_message_text("Ссылка не найдена.")

    mode = query.data.split("_")[1]
    await query.edit_message_text(get_txt(user_id, "dl_start"))

    if mode == "video":
        out_file = f"video_{user_id}.mp4"
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': out_file,
            'quiet': True,
            'socket_timeout': 15
        }
        try:
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            ydl.download([url])
            if os.path.exists(out_file):
                with open(out_file, "rb") as f:
                    await update.effective_message.reply_video(video=f)
                db["stats"]["video"] += 1
                save_db()
                os.remove(out_file)
                await query.delete_message()
            else:
                await query.edit_message_text(get_txt(user_id, "dl_err"))
        except Exception:
            await query.edit_message_text(get_txt(user_id, "dl_err"))

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
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            ydl.download([url])
            if os.path.exists(out_file):
                with open(out_file, "rb") as f:
                    await update.effective_message.reply_audio(audio=f)
                db["stats"]["music"] += 1
                save_db()
                os.remove(out_file)
                await query.delete_message()
            else:
                await query.edit_message_text(get_txt(user_id, "dl_err"))
        except Exception:
            await query.edit_message_text(get_txt(user_id, "dl_err"))

async def video_to_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    msg = await update.message.reply_text("⏳ Создаю кружочек...")
    
    in_path = f"in_{user_id}.mp4"
    out_path = f"out_{user_id}.mp4"

    video_file = await update.message.video.get_file()
    await video_file.download_to_drive(in_path)

    cmd = f'ffmpeg -y -i "{in_path}" -vf "crop=min(iw\\,ih):min(iw\\,ih),scale=480:480:force_original_aspect_ratio=decrease" -c:v libx264 -crf 26 -preset ultrafast -c:a aac -b:a 128k "{out_path}"'
    os.system(cmd)

    if os.path.exists(out_path):
        with open(out_path, "rb") as f:
            await update.message.reply_video_note(video_note=f)
        db["stats"]["note"] += 1
        save_db()
        os.remove(out_path)
    else:
        await update.message.reply_text("❌ Ошибка обработки видео.")

    if os.path.exists(in_path):
        os.remove(in_path)
    await msg.delete()

async def note_to_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    msg = await update.message.reply_text("⏳ Преобразую в видео...")
    
    in_path = f"note_in_{user_id}.mp4"
    note_file = await update.message.video_note.get_file()
    await note_file.download_to_drive(in_path)

    if os.path.exists(in_path):
        with open(in_path, "rb") as f:
            await update.message.reply_video(video=f)
        os.remove(in_path)
        await msg.delete()
    else:
        await msg.edit_text("❌ Ошибка при конвертации.")

async def photo_to_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    file_path = f"sticker_{user_id}.webp"
    
    photo_file = await update.message.photo[-1].get_file()
    await photo_file.download_to_drive(file_path)

    with open(file_path, "rb") as f:
        await update.message.reply_sticker(sticker=f)
    
    db["stats"]["sticker"] += 1
    save_db()
    os.remove(file_path)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("lang", lang_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("say", say_cmd))
    app.add_handler(CommandHandler("music", music_cmd))
    
    app.add_handler(CallbackQueryHandler(set_lang, pattern=r"^lang_"))
    app.add_handler(CallbackQueryHandler(process_dl, pattern=r"^dl_"))
    
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'https?://[^\s]+'), link_handler))
    app.add_handler(MessageHandler(filters.VIDEO, video_to_note))
    app.add_handler(MessageHandler(filters.VIDEO_NOTE, note_to_video))
    app.add_handler(MessageHandler(filters.PHOTO, photo_to_sticker))

    app.run_polling()

if __name__ == "__main__":
    main()
