import os
import asyncio
import logging
import static_ffmpeg
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, ReplyKeyboardRemove, BotCommand
from elevenlabs.client import ElevenLabs
import yt_dlp

static_ffmpeg.add_paths()

BOT_TOKEN = "8765852488:AAErO2_3gbQCR8UG7AncX64p2d3W3z5W0Tg"
ELEVENLABS_API_KEY = "sk_053e9cf42e316b2532d4ed3c2049d29622ec80f81d7fe01d"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

client_11labs = ElevenLabs(api_key=ELEVENLABS_API_KEY)
os.makedirs("downloads", exist_ok=True)

user_languages = {}
users_list = set()
stats_counter = {"videos": 0, "audio": 0, "stickers": 0, "notes": 0, "searches": 0, "tts": 0}

# Идентификаторы 4 популярнейших голосов ElevenLabs
VOICES = {
    "voice_grandpa": {"id": "N2lNodeNq1ol5D28583Z", "name": "👴 Дедушка / Bobo"},
    "voice_robot": {"id": "onwK4e9ZLuTAKqWW03F9", "name": "🤖 Робот / Robot"},
    "voice_narrator": {"id": "pNInz6ovcgqXgE806mWg", "name": "🎙 Диктор (Адам)"},
    "voice_female": {"id": "21m00Tcm4TlvDq8ikWAM", "name": "👩 Женский (Рэйчел)"}
}

pending_say_texts = {}

TEXTS = {
    "ru": {
        "start": (
            "🚀 **Привет! Я твой универсальный медиа-помощник.**\n\n"
            "✨ **Мои возможности:**\n"
            "1. 📥 **Скачивание по ссылке** — отправь ссылку (TikTok/Reels/Shorts) и скачай Видео или MP3.\n"
            "2. 🔎 **Поиск музыки** — напиши `/music Название`, и я найду MP3!\n"
            "3. 🔄 **Видео в кружочек** — отправь видео для создания кружочка.\n"
            "4. 🖼 **Фото в стикер** — отправь картинку.\n"
            "5. 🗣 **ИИ Озвучка текста** — напиши `/say Текст` и выбери голос!"
        ),
        "say_no_text": "⚠️ Напишите текст после команды, например: `/say Привет, как дела?`",
        "choose_voice": "🎙 **Выберите голос для озвучки:**",
        "tts_generating": "🗣 Генерирую голосом ElevenLabs...",
        "media_ask": "🎬 Что сделать с этим видео?",
        "btn_note": "🔄 Сделать кружочек",
        "btn_extract_mp3": "🎵 Извлечь MP3",
        "processing": "⏳ Обрабатываю...",
        "not_found": "❌ Ничего не найдено."
    },
    "uz": {
        "start": (
            "🚀 **Salom! Men sizning universal media yordamchingizman.**\n\n"
            "✨ **Imkoniyatlarim:**\n"
            "1. 📥 **Havola orqali yuklash** — TikTok/Reels/Shorts havolasini yuboring.\n"
            "2. 🔎 **Musiqa qidirish** — `/music Nomi` deb yozing.\n"
            "3. 🔄 **Videoni dumaloq qilish** — video yuboring.\n"
            "4. 🖼 **Rasmdan stiker** — rasm yuboring.\n"
            "5. 🗣 **AI Ovozli matn** — `/say Matn` deb yozing va ovozni tanlang!"
        ),
        "say_no_text": "⚠️ Buyruqdan so'ng matn yozing: `/say Salom`",
        "choose_voice": "🎙 **Ovoz turini tanlang:**",
        "tts_generating": "🗣 ElevenLabs AI ovozi yaratilmoqda...",
        "media_ask": "🎬 Videoni nima qilamiz?",
        "btn_note": "🔄 Dumaloq video (Krujochek)",
        "btn_extract_mp3": "🎵 MP3 ajratish",
        "processing": "⏳ Ishlanmoqda...",
        "not_found": "❌ Topilmadi."
    }
}

def get_text(user_id: int, key: str) -> str:
    lang = user_languages.get(user_id, "ru")
    return TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, ""))

# --- Веб-сервер от сна Render ---
async def handle_ping(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/ping", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- Хэндлеры ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    users_list.add(message.from_user.id)
    text = get_text(message.from_user.id, "start")
    await message.answer(text, reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")

@dp.message(Command("say"))
async def text_to_speech_handler(message: types.Message):
    user_id = message.from_user.id
    users_list.add(user_id)
    text = message.text.replace("/say", "").strip()
    
    if not text:
        return await message.answer(get_text(user_id, "say_no_text"), parse_mode="Markdown")
    
    pending_say_texts[user_id] = text
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="👴 Дедушка / Bobo", callback_data="voice_grandpa"),
            types.InlineKeyboardButton(text="🤖 Робот / Robot", callback_data="voice_robot")
        ],
        [
            types.InlineKeyboardButton(text="🎙 Диктор (Адам)", callback_data="voice_narrator"),
            types.InlineKeyboardButton(text="👩 Женский (Рэйчел)", callback_data="voice_female")
        ]
    ])
    
    await message.answer(get_text(user_id, "choose_voice"), reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("voice_"))
async def generate_voice_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    voice_key = callback.data
    text = pending_say_texts.get(user_id)
    
    if not text:
        await callback.answer("⚠️ Текст не найден. Напишите /say заново.", show_alert=True)
        return
    
    status_msg = await callback.message.edit_text(get_text(user_id, "tts_generating"))
    output_audio = f"downloads/{user_id}_tts.mp3"
    
    try:
        voice_info = VOICES.get(voice_key, VOICES["voice_narrator"])
        
        # Модель eleven_multilingual_v2 отлично произносит и узбекский, и русский без акцента
        audio = client_11labs.generate(
            text=text,
            voice=voice_info["id"],
            model="eleven_multilingual_v2"
        )
        
        with open(output_audio, "wb") as f:
            for chunk in audio:
                f.write(chunk)
                
        if os.path.exists(output_audio):
            await callback.message.answer_audio(
                FSInputFile(output_audio),
                caption=f"🗣 **Голос:** {voice_info['name']}\n💬 **Текст:** _{text}_",
                parse_mode="Markdown"
            )
            stats_counter['tts'] += 1
            os.remove(output_audio)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Ошибка при генерации аудио.")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка ElevenLabs: {str(e)}")
        
    await callback.answer()

@dp.message(F.video | F.document)
async def media_file_handler(message: types.Message):
    users_list.add(message.from_user.id)
    user_id = message.from_user.id
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text=get_text(user_id, "btn_note"), callback_data="convert_note"),
            types.InlineKeyboardButton(text=get_text(user_id, "btn_extract_mp3"), callback_data="convert_mp3")
        ]
    ])
    await message.answer(get_text(user_id, "media_ask"), reply_markup=kb, reply_to_message_id=message.message_id)

@dp.callback_query(F.data.in_({"convert_note", "convert_mp3"}))
async def process_media_file(callback: types.CallbackQuery):
    msg = callback.message.reply_to_message
    file_id = msg.video.file_id if msg.video else msg.document.file_id
    user_id = callback.from_user.id
    
    status_msg = await callback.message.edit_text(get_text(user_id, "processing"))
    file = await bot.get_file(file_id)
    input_file = f"downloads/{user_id}_input.mp4"
    await bot.download_file(file.file_path, input_file)
    
    if callback.data == "convert_note":
        output_note = f"downloads/{user_id}_note.mp4"
        # Точный 1:1 квадрат по центру + конвертация под стандарт кружочков Telegram
        ffmpeg_cmd = f'ffmpeg -y -i {input_file} -vf "crop=min(iw\,ih):min(iw\,ih),scale=640:640" -c:v libx264 -crf 28 -preset ultrafast -c:a aac -b:a 128k {output_note}'
        process = await asyncio.create_subprocess_shell(ffmpeg_cmd)
        await process.communicate()
        
        if os.path.exists(output_note):
            await callback.message.answer_video_note(FSInputFile(output_note))
            stats_counter['notes'] += 1
            await status_msg.delete()
            os.remove(output_note)
        else:
            await status_msg.edit_text("❌ Ошибка создания кружочка.")
            
    elif callback.data == "convert_mp3":
        output_mp3 = f"downloads/{user_id}_audio.mp3"
        ffmpeg_cmd = f'ffmpeg -y -i {input_file} -vn -acodec libmp3lame -q:a 2 {output_mp3}'
        process = await asyncio.create_subprocess_shell(ffmpeg_cmd)
        await process.communicate()
        
        if os.path.exists(output_mp3):
            await callback.message.answer_audio(FSInputFile(output_mp3), caption="🎵 MP3")
            stats_counter['audio'] += 1
            await status_msg.delete()
            os.remove(output_mp3)

    if os.path.exists(input_file):
        os.remove(input_file)
    await callback.answer()

@dp.message(Command("music"))
async def search_music_handler(message: types.Message):
    users_list.add(message.from_user.id)
    query = message.text.replace("/music", "").strip()
    user_id = message.from_user.id
    
    if not query:
        return await message.answer("⚠️ Напишите название песни: `/music Miyagi`", parse_mode="Markdown")
    
    status_msg = await message.answer(f"🔎 Ищу: **{query}**...", parse_mode="Markdown")
    output_path = f"downloads/{user_id}_search.mp3"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'default_search': 'scsearch1:',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
    }
    
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([query]))
        if not os.path.exists(output_path) and os.path.exists(output_path + ".mp3"):
            output_path += ".mp3"

        if os.path.exists(output_path):
            await message.answer_audio(FSInputFile(output_path), caption=f"🎵 **{query}**", parse_mode="Markdown")
            stats_counter['searches'] += 1
            stats_counter['audio'] += 1
            os.remove(output_path)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Не найдено.")
    except Exception:
        await status_msg.edit_text("❌ Ошибка при поиске.")

@dp.message(Command("lang"))
async def lang_cmd(message: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            types.InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")
        ]
    ])
    await message.answer("🌐 Выберите язык / Tilingizni tanlang:", reply_markup=kb)

@dp.callback_query(F.data.startswith("lang_"))
async def set_language_callback(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_languages[callback.from_user.id] = lang
    responses = {"ru": "✅ Язык изменен на Русский!", "uz": "✅ Tilingiz O'zbekchaga o'zgartirildi!"}
    await callback.message.edit_text(responses.get(lang, "✅ OK"))
    await callback.answer()

@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):
    text = (
        "📊 **Статистика бота:**\n\n"
        f"👥 Пользователи: `{len(users_list)}`\n"
        f"🔎 Найдено песен: `{stats_counter['searches']}`\n"
        f"🗣 Озвучено ElevenLabs: `{stats_counter['tts']}`\n"
        f"🎬 Скачано видео: `{stats_counter['videos']}`\n"
        f"🔄 Кружочки: `{stats_counter['notes']}`\n"
        f"🖼 Стикеры: `{stats_counter['stickers']}`"
    )
    await message.answer(text, parse_mode="Markdown")

async def main():
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
