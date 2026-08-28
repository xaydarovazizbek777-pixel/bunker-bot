import os
import json
import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import yt_dlp
import static_ffmpeg

# Автоматическая настройка FFmpeg
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
        "stats": {"music": 0, "video": 0, "note": 0, "sticker": 0}
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
        "start": "🚀 **Media Save Bot**\n\nОтправь мне ссылку на Reels, TikTok или Shorts, либо отправь видео/фото!\n\n📌 Нажми /help для просмотра всех команд.",
        "help": "ℹ️ **Инструкция по командам:**\n\n📩 **Скачивание:** Отправь ссылку на TikTok, Reels или Shorts ➔ выбери видео или MP3.\n🔍 `/music Название` — Найти и скачать песню.\n🔄 **Видео ➔ Кружок:** Отправь обычное видео.\n🔄 **Кружок ➔ Видео:** Отправь круглое видеосообщение.\n🖼 **Фото ➔ Стикер:** Отправь любое изображение.\n🌐 `/lang` — Сменить язык.\n📊 `/stats` — Статистика (только админ).",
        "lang_select": "🌐 Выберите язык / Tilingizni tanlang:",
        "lang_set": "✅ Язык успешно изменен на Русский!",
        "stats": "📊 **Статистика бота:**\n\n👥 Всего пользователей: {users}\n🔍 Скачано музыки: {music}\n🎬 Скачано видео по ссылкам: {video}\n🔄 Сделано кружочков: {note}\n🖼 Превращено в стикеры: {sticker}",
        "no_access": "⛔ Команда доступна только владельцу бота.",
        "music_prompt": "⚠️ Укажите название трека: `/music Miyagi`",
        "music_search": "🔎 Ищу и загружаю трек...",
        "music_err": "❌ Не удалось скачать трек.",
        "dl_prompt": "🎬 Выберите формат для скачивания:",
        "dl_start": "⏳ Скачиваю файл...",
        "dl_err": "❌ Ошибка скачивания по этой ссылке."
    },
    "uz": {
        "start": "🚀 **Media Save Bot**\n\nMenga Reels, TikTok yoki Shorts havolasini yuboring!\n\n📌 Buyruqlar ro'yxati uchun /help tugmasini bosing.",
        "help": "ℹ️ **Botdan foydalanish yo'riqnomasi:**\n\n📩 **Yuklab olish:** TikTok, Reels yoki Shorts havolasini yuboring ➔ formatni tanlang.\n🔍 `/music Nomi` — Musiqa qidirish va yuklash.\n🔄 **Video ➔ Dumaloq video:** Oddiy video yuboring.\n🔄 **Dumaloq video ➔ Oddiy video:** Dumaloq video yuboring.\n🖼 **Rasm ➔ Stiker:** Rasm yuboring.\n🌐 `/lang` — Tilni o'zgartirish.\n📊 `/stats` — Bot statistikasi (faqat admin uchun).",
        "lang_select": "🌐 Выберите язык / Tilingizni tanlang:",
        "lang_set": "✅ Tilingiz O'zbekchaga o'zgartirildi!",
        "stats": "📊 **Bot statistikasi:**\n\n👥 Foydalanuvchilar: {users}\n🔍 Musiqa yuklangan: {music}\n🎬 Video yuklangan: {video}\n🔄 Dumaloq videolar: {note}\n🖼 Stikerlar: {sticker}",
        "no_access": "⛔ Bu buyruq faqat bot egasi uchun.",
        "music_prompt": "⚠️ Qo'shiq nomini kiriting: `/music Miyagi`",
        "music_search": "🔎 Qidirilmoqda va yuklanmoqda...",
        "music_err": "❌ Yuklab bo'lmadi.",
        "dl_prompt": "🎬 Yuklab olish formatini tanlang:",
        "dl_start": "⏳ Yuklanmoqda...",
        "dl_err": "❌ Ushbu havoladan yuklab bo'lmadi."
    }
}

def get_txt(user_id, key):
    lang = get_lang(user_id)
    return TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"][key])

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    await update.message.reply_text(get_txt(user_id, "start"), parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    await update.message.reply_text(get_txt(user_id, "help"), parse_mode="Markdown")

async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")]
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
        video=s["video"],
        note=s["note"],
        sticker=s["sticker"]
    )
    await update.message.reply_text(text, parse_mode="Markdown")

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

    def run_download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([query])

    try:
        await asyncio.to_thread(run_download)
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
        return await query.edit_message_text("Ссылка устарела. Отправьте её еще раз.")

    mode = query.data.split("_")[1]
    await query.edit_message_text(get_txt(user_id, "dl_start"))

    if mode == "video":
        out_file = f"video_{user_id}.mp4"
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': out_file,
            'quiet': True,
            'socket_timeout': 20
        }
        def dl_v():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        try:
            await asyncio.to_thread(dl_v)
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
            'socket_timeout': 20
        }
        def dl_a():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        try:
            await asyncio.to_thread(dl_a)
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
    msg = await update.message.reply_text("⏳ Преобразую в кружочек...")
    
    in_path = f"in_{user_id}.mp4"
    out_path = f"out_{user_id}.mp4"

    video_file = await update.message.video.get_file()
    await video_file.download_to_drive(in_path)

    def convert():
        cmd = f'ffmpeg -y -i "{in_path}" -vf "crop=min(iw\\,ih):min(iw\\,ih),scale=480:480:force_original_aspect_ratio=decrease" -c:v libx264 -crf 26 -preset ultrafast -c:a aac -b:a 128k "{out_path}"'
        os.system(cmd)

    await asyncio.to_thread(convert)

    if os.path.exists(out_path):
        with open(out_path, "rb") as f:
            await update.message.reply_video_note(video_note=f)
        db["stats"]["note"] += 1
        save_db()
        os.remove(out_path)
    else:
        await update.message.reply_text("❌ Ошибка при создании кружочка.")

    if os.path.exists(in_path):
        os.remove(in_path)
    await msg.delete()

async def note_to_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    msg = await update.message.reply_text("⏳ Распаковываю в обычное видео...")
    
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
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("lang", lang_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("music", music_cmd))
    
    app.add_handler(CallbackQueryHandler(set_lang, pattern=r"^lang_"))
    app.add_handler(CallbackQueryHandler(process_dl, pattern=r"^dl_"))
    
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'https?://[^\s]+'), link_handler))
    app.add_handler(MessageHandler(filters.VIDEO & ~filters.VIDEO_NOTE, video_to_note))
    app.add_handler(MessageHandler(filters.VIDEO_NOTE, note_to_video))
    app.add_handler(MessageHandler(filters.PHOTO, photo_to_sticker))

    app.run_polling()

if __name__ == "__main__":
    main()
