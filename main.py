import os
import asyncio
import logging
import static_ffmpeg
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, ReplyKeyboardRemove, BotCommand
from gtts import gTTS
import yt_dlp

# Инициализируем ffmpeg
static_ffmpeg.add_paths()

BOT_TOKEN = "8765852488:AAErO2_3gbQCR8UG7AncX64p2d3W3z5W0Tg"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

os.makedirs("downloads", exist_ok=True)

user_languages = {}
users_list = set()
stats_counter = {"videos": 0, "audio": 0, "stickers": 0, "notes": 0, "searches": 0}

TEXTS = {
    "ru": {
        "start": (
            "🚀 **Привет! Я твой универсальный медиа-помощник.**\n\n"
            "✨ **Мои возможности:**\n"
            "1. 📥 **Скачивание по ссылке** — отправь ссылку (TikTok/Reels/Shorts) и скачай Видео или MP3.\n"
            "2. 🔎 **Поиск музыки** — напиши `/music Название` (например `/music Miyagi`), и я найду MP3!\n"
            "3. 🔄 **Видео в кружочек** — отправь видео, чтобы сделать круглое видеосообщение.\n"
            "4. 🖼 **Фото в стикер** — отправь картинку, чтобы получить Telegram-стикер.\n"
            "5. 🗣 **Озвучка текста** — напиши `/say Текст`."
        ),
        "ask_download": "🎯 **Что вы хотите скачать по этой ссылке?**",
        "btn_video": "🎬 Видео (MP4)",
        "btn_audio": "🎵 Аудио (MP3)",
        "downloading": "⏳ Идет скачивание...",
        "video_ready": "✅ Ваше видео готово!",
        "audio_ready": "✅ Ваш трек в формате MP3!",
        "search_no_query": "⚠️ Напишите название песни после команды.\nПример: `/music Miyagi Captain`",
        "searching": "🔎 Ищу песню: **{query}**...",
        "found_music": "🎵 Найдено по запросу: **{query}**",
        "not_found": "❌ Песня не найдена. Попробуйте уточнить название.",
        "sticker_processing": "🎨 Превращаю картинку в стикер...",
        "media_ask": "🎬 Что сделать с этим видео?",
        "btn_note": "🔄 Сделать кружочек",
        "btn_extract_mp3": "🎵 Извлечь MP3",
        "processing": "⏳ Обрабатываю файл...",
        "say_no_text": "⚠️ Напишите текст после команды, например: `/say Привет`",
        "help": (
            "❓ **Как со мной работать:**\n\n"
            "• **Найти песню:** Напишите `/music Название трека`.\n"
            "• **Скачать видео/музыку:** Отправьте ссылку из TikTok, Reels или Shorts.\n"
            "• **Сделать стикер:** Пришлите фотографию.\n"
            "• **Сделать кружочек:** Пришлите видеофайл.\n"
            "• **Озвучить текст:** Напишите `/say Текст`"
        )
    },
    "uz": {
        "start": (
            "🚀 **Salom! Men sizning universal media yordamchingizman.**\n\n"
            "✨ **Imkoniyatlarim:**\n"
            "1. 📥 **Havola orqali yuklash** — TikTok/Reels/Shorts havolasini yuboring va Video yoki MP3 yuklang.\n"
            "2. 🔎 **Musiqa qidirish** — `/music Nomi` deb yozing (masalan `/music Miyagi`) va MP3 oling!\n"
            "3. 🔄 **Videoni dumaloq qilish** — videoni domaloq shaklga o'tkazish uchun yuboring.\n"
            "4. 🖼 **Rasmdan stiker** — stiker yaratish uchun rasm yuboring.\n"
            "5. 🗣 **Matnni ovozga o'tkazish** — `/say Matn` deb yozing."
        ),
        "ask_download": "🎯 **Ushbu havola orqali nimani yuklab olmoqchisiz?**",
        "btn_video": "🎬 Video (MP4)",
        "btn_audio": "🎵 Audio (MP3)",
        "downloading": "⏳ Yuklab olinmoqda...",
        "video_ready": "✅ Videongiz tayyor!",
        "audio_ready": "✅ Audioyingiz MP3 formatida tayyor!",
        "search_no_query": "⚠️ Buyruqdan so'ng qo'shiq nomini yozing.\nMasalan: `/music Miyagi Captain`",
        "searching": "🔎 Qidirilmoqda: **{query}**...",
        "found_music": "🎵 Qidiruv bo'yicha topildi: **{query}**",
        "not_found": "❌ Qo'shiq topilmadi. Nomini aniqroq yozib ko'ring.",
        "sticker_processing": "🎨 Rasm stikerga aylantirilmoqda...",
        "media_ask": "🎬 Ushbu video bilan nima qilmoqchisiz?",
        "btn_note": "🔄 Dumaloq video qilish",
        "btn_extract_mp3": "🎵 MP3 ajratib olish",
        "processing": "⏳ Fayl qayta ishlanmoqda...",
        "say_no_text": "⚠️ Buyruqdan so'ng matn yozing, masalan: `/say Salom`",
        "help": (
            "❓ **Men bilan ishlash bo'yicha yo'riqnoma:**\n\n"
            "• **Musiqa qidirish:** `/music Qo'shiq nomi` deb yozing.\n"
            "• **Video/Audio yuklash:** TikTok, Reels yoki Shorts havolasini yuboring.\n"
            "• **Stiker qilish:** Rasm yuboring.\n"
            "• **Dumaloq video qilish:** Video yuboring.\n"
            "• **Ovozli matn:** `/say Matn` deb yozing."
        )
    },
    "en": {
        "start": (
            "🚀 **Hello! I am your universal media assistant.**\n\n"
            "✨ **Features:**\n"
            "1. 📥 **Download by link** — send TikTok/Reels/Shorts link to get Video or MP3.\n"
            "2. 🔎 **Search Music** — type `/music Title` (e.g. `/music Miyagi`) to download MP3!\n"
            "3. 🔄 **Video Note** — send a video to convert it into a video note (circle).\n"
            "4. 🖼 **Photo to Sticker** — send an image to get a Telegram sticker.\n"
            "5. 🗣 **Text to Speech** — type `/say Text`."
        ),
        "ask_download": "🎯 **What do you want to download from this link?**",
        "btn_video": "🎬 Video (MP4)",
        "btn_audio": "🎵 Audio (MP3)",
        "downloading": "⏳ Downloading...",
        "video_ready": "✅ Your video is ready!",
        "audio_ready": "✅ Your audio is ready in MP3!",
        "search_no_query": "⚠️ Please write the song title after the command.\nExample: `/music Miyagi Captain`",
        "searching": "🔎 Searching for song: **{query}**...",
        "found_music": "🎵 Found for query: **{query}**",
        "not_found": "❌ Song not found. Try clarifying the title.",
        "sticker_processing": "🎨 Converting photo to sticker...",
        "media_ask": "🎬 What would you like to do with this video?",
        "btn_note": "🔄 Make Video Note",
        "btn_extract_mp3": "🎵 Extract MP3",
        "processing": "⏳ Processing file...",
        "say_no_text": "⚠️ Please write text after command, e.g.: `/say Hello`",
        "help": (
            "❓ **How to use me:**\n\n"
            "• **Find Song:** Type `/music Song Title`.\n"
            "• **Download Video/Music:** Send TikTok, Reels, or Shorts link.\n"
            "• **Make Sticker:** Send a photo.\n"
            "• **Make Video Note:** Send a video file.\n"
            "• **Text to Speech:** Type `/say Text`"
        )
    }
}

def get_text(user_id: int, key: str) -> str:
    lang = user_languages.get(user_id, "ru")
    return TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, ""))

async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="start", description="🚀 Start / Main Menu"),
        BotCommand(command="music", description="🔎 Search Music (/music title)"),
        BotCommand(command="say", description="🗣 Text to Speech (/say hello)"),
        BotCommand(command="lang", description="🌐 Language / Язык / Til"),
        BotCommand(command="stats", description="📊 Statistics"),
        BotCommand(command="help", description="❓ Help / Info"),
    ]
    await bot.set_my_commands(main_menu_commands)

def register_user(user_id: int):
    users_list.add(user_id)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    register_user(message.from_user.id)
    text = get_text(message.from_user.id, "start")
    await message.answer(text, reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")

@dp.message(Command("music"))
async def search_music_handler(message: types.Message):
    register_user(message.from_user.id)
    query = message.text.replace("/music", "").strip()
    user_id = message.from_user.id
    
    if not query:
        return await message.answer(get_text(user_id, "search_no_query"), parse_mode="Markdown")
    
    status_msg = await message.answer(get_text(user_id, "searching").format(query=query), parse_mode="Markdown")
    output_path = f"downloads/{user_id}_search.mp3"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'default_search': 'ytsearch1:',
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([query]))
        
        if not os.path.exists(output_path) and os.path.exists(output_path + ".mp3"):
            output_path += ".mp3"

        if os.path.exists(output_path):
            await message.answer_audio(FSInputFile(output_path), caption=get_text(user_id, "found_music").format(query=query), parse_mode="Markdown")
            stats_counter['searches'] += 1
            stats_counter['audio'] += 1
            os.remove(output_path)
            await status_msg.delete()
        else:
            await status_msg.edit_text(get_text(user_id, "not_found"))
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

@dp.message(Command("lang"))
async def lang_cmd(message: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            types.InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
            types.InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
        ]
    ])
    await message.answer("🌐 Выберите язык / Tilingizni tanlang / Choose language:", reply_markup=kb)

@dp.callback_query(F.data.startswith("lang_"))
async def set_language_callback(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_languages[callback.from_user.id] = lang
    responses = {
        "ru": "✅ Язык успешно изменен на Русский!",
        "uz": "✅ Tilingiz O'zbekchaga muvaffaqiyatli o'zgartirildi!",
        "en": "✅ Language successfully changed to English!"
    }
    await callback.message.edit_text(responses.get(lang, "✅ OK"))
    await callback.answer()

@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):
    text = (
        "📊 **Статистика бота:**\n\n"
        f"👥 Всего пользователей: `{len(users_list)}`\n"
        f"🔎 Найдено песен (/music): `{stats_counter['searches']}`\n"
        f"🎬 Скачано видео: `{stats_counter['videos']}`\n"
        f"🎵 Всего MP3 отправлено: `{stats_counter['audio']}`\n"
        f"🔄 Сделано кружочков: `{stats_counter['notes']}`\n"
        f"🖼 Создано стикеров: `{stats_counter['stickers']}`"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(get_text(message.from_user.id, "help"), parse_mode="Markdown")

@dp.message(F.text.startswith("http://") | F.text.startswith("https://"))
async def ask_download_format(message: types.Message):
    register_user(message.from_user.id)
    user_id = message.from_user.id
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text=get_text(user_id, "btn_video"), callback_data="dl_video"),
            types.InlineKeyboardButton(text=get_text(user_id, "btn_audio"), callback_data="dl_audio")
        ]
    ])
    await message.answer(get_text(user_id, "ask_download"), reply_markup=kb, reply_to_message_id=message.message_id, parse_mode="Markdown")

@dp.callback_query(F.data.in_({"dl_video", "dl_audio"}))
async def process_download(callback: types.CallbackQuery):
    url = callback.message.reply_to_message.text.strip()
    action = callback.data
    user_id = callback.from_user.id
    
    status_msg = await callback.message.edit_text(get_text(user_id, "downloading"))
    
    if action == "dl_video":
        output_path = f"downloads/{user_id}_video.mp4"
        ydl_opts = {
            'format': 'mp4/best',
            'outtmpl': output_path,
            'quiet': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
        }
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
            if os.path.exists(output_path):
                await callback.message.answer_video(FSInputFile(output_path), caption=get_text(user_id, "video_ready"))
                stats_counter['videos'] += 1
                os.remove(output_path)
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ Ошибка при скачивании.")
        except Exception as e:
            await status_msg.edit_text(f"❌ Error: {str(e)}")
            
    elif action == "dl_audio":
        output_path = f"downloads/{user_id}_audio.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
            
            if not os.path.exists(output_path) and os.path.exists(output_path + ".mp3"):
                output_path += ".mp3"

            if os.path.exists(output_path):
                await callback.message.answer_audio(FSInputFile(output_path), caption=get_text(user_id, "audio_ready"))
                stats_counter['audio'] += 1
                os.remove(output_path)
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ Ошибка при скачивании.")
        except Exception as e:
            await status_msg.edit_text(f"❌ Error: {str(e)}")
            
    await callback.answer()

@dp.message(F.photo)
async def photo_to_sticker_handler(message: types.Message):
    register_user(message.from_user.id)
    user_id = message.from_user.id
    status_msg = await message.answer(get_text(user_id, "sticker_processing"))
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    
    input_path = f"downloads/{user_id}_img.jpg"
    output_sticker = f"downloads/{user_id}_sticker.webp"
    
    await bot.download_file(file.file_path, input_path)
    
    ffmpeg_cmd = f'ffmpeg -y -i {input_path} -vf "scale=512:512:force_original_aspect_ratio=decrease" {output_sticker}'
    process = await asyncio.create_subprocess_shell(ffmpeg_cmd)
    await process.communicate()
    
    if os.path.exists(output_sticker):
        await message.answer_sticker(FSInputFile(output_sticker))
        stats_counter['stickers'] += 1
        await status_msg.delete()
        os.remove(input_path)
        os.remove(output_sticker)
    else:
        await status_msg.edit_text("❌ Error creating sticker.")

@dp.message(F.video | F.document)
async def media_file_handler(message: types.Message):
    register_user(message.from_user.id)
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
        ffmpeg_cmd = f'ffmpeg -y -i {input_file} -vf "crop=ih:ih,scale=640:640" -c:v libx264 -crf 26 -preset ultrafast -c:a aac {output_note}'
        process = await asyncio.create_subprocess_shell(ffmpeg_cmd)
        await process.communicate()
        
        if os.path.exists(output_note):
            await callback.message.answer_video_note(FSInputFile(output_note))
            stats_counter['notes'] += 1
            await status_msg.delete()
            os.remove(output_note)
        else:
            await status_msg.edit_text("❌ Error creating note.")
            
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
        else:
            await status_msg.edit_text("❌ Error extracting MP3.")

    if os.path.exists(input_file):
        os.remove(input_file)
    await callback.answer()

@dp.message(F.text.startswith("/say"))
async def text_to_speech_handler(message: types.Message):
    register_user(message.from_user.id)
    user_id = message.from_user.id
    text = message.text.replace("/say", "").strip()
    if not text:
        return await message.answer(get_text(user_id, "say_no_text"), parse_mode="Markdown")
    output_audio = f"downloads/{user_id}_audio.ogg"
    
    lang = user_languages.get(user_id, "ru")
    tts_lang = "ru" if lang == "ru" else ("en" if lang == "en" else "uz" if lang == "uz" else "ru")
    
    try:
        gTTS(text=text, lang=tts_lang).save(output_audio)
        await message.answer_voice(FSInputFile(output_audio))
        os.remove(output_audio)
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)}")

async def main():
    await set_main_menu(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
