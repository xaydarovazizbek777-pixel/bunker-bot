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

# Новый токен твоего бота
BOT_TOKEN = "8765852488:AAErO2_3gbQCR8UG7AncX64p2d3W3z5W0Tg"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

os.makedirs("downloads", exist_ok=True)

user_languages = {}
users_list = set()
stats_counter = {"videos": 0, "audio": 0, "stickers": 0, "notes": 0, "searches": 0}

# Меню команд в Telegram (при нажатии на /)
async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="start", description="🚀 Главное меню / Перезапуск"),
        BotCommand(command="music", description="🔎 Найти и скачать музыку (/music название)"),
        BotCommand(command="say", description="🗣 Озвучить текст (/say привет)"),
        BotCommand(command="lang", description="🌐 Сменить язык / Change language"),
        BotCommand(command="stats", description="📊 Статистика использования"),
        BotCommand(command="help", description="❓ Инструкция"),
    ]
    await bot.set_my_commands(main_menu_commands)

def register_user(user_id: int):
    users_list.add(user_id)

# Команда /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    register_user(message.from_user.id)
    text = (
        "🚀 **Привет! Я твой универсальный медиа-помощник.**\n\n"
        "✨ **Мои возможности:**\n"
        "1. 📥 **Скачивание по ссылке** — отправь ссылку (TikTok/Reels/Shorts) и скачай Видео или MP3.\n"
        "2. 🔎 **Поиск музыки** — напиши `/music Название` (например `/music Miyagi`), и я найду MP3!\n"
        "3. 🔄 **Видео в кружочек** — отправь видео, чтобы сделать круглое видеосообщение.\n"
        "4. 🖼 **Фото в стикер** — отправь картинку, чтобы получить Telegram-стикер.\n"
        "5. 🗣 **Озвучка текста** — напиши `/say Текст`."
    )
    await message.answer(text, reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")

# Команда /music - Поиск и скачивание любой музыки по названию
@dp.message(Command("music"))
async def search_music_handler(message: types.Message):
    register_user(message.from_user.id)
    query = message.text.replace("/music", "").strip()
    
    if not query:
        return await message.answer("⚠️ Напиши название песни после команды.\nПример: `/say /music Miyagi Captain`", parse_mode="Markdown")
    
    status_msg = await message.answer(f"🔎 Ищу песню: **{query}**...", parse_mode="Markdown")
    user_id = message.from_user.id
    output_path = f"downloads/{user_id}_search.mp3"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'default_search': 'ytsearch1:',  # Ищет первое совпадение на YouTube
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
            await message.answer_audio(FSInputFile(output_path), caption=f"🎵 Найдено по запросу: **{query}**", parse_mode="Markdown")
            stats_counter['searches'] += 1
            stats_counter['audio'] += 1
            os.remove(output_path)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Песня не найдена. Попробуй уточнить название.")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка при поиске: {str(e)}")

# Команда /lang
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
        "ru": "✅ Язык изменен на Русский!",
        "uz": "✅ Tilingiz O'zbekchaga o'zgartirildi!",
        "en": "✅ Language changed to English!"
    }
    await callback.message.edit_text(responses.get(lang, "✅ OK"))
    await callback.answer()

# Команда /stats
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

# Команда /help
@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        "❓ **Как со мной работать:**\n\n"
        "• **Найти песню:** Напиши `/music Название трека`.\n"
        "• **Скачать видео/музыку по ссылке:** Отправь ссылку из TikTok, Reels или Shorts.\n"
        "• **Сделать стикер:** Пришли фотографию.\n"
        "• **Сделать кружочек:** Пришли видеофайл.\n"
        "• **Озвучить текст:** Напиши `/say Текст`"
    )

# Выбор формата скачивания по ссылке
@dp.message(F.text.startswith("http://") | F.text.startswith("https://"))
async def ask_download_format(message: types.Message):
    register_user(message.from_user.id)
    url = message.text.strip()
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🎬 Видео (MP4)", callback_data="dl_video"),
            types.InlineKeyboardButton(text="🎵 Аудио (MP3)", callback_data="dl_audio")
        ]
    ])
    await message.answer("🎯 **Что вы хотите скачать по этой ссылке?**", reply_markup=kb, reply_to_message_id=message.message_id)

@dp.callback_query(F.data.in_({"dl_video", "dl_audio"}))
async def process_download(callback: types.CallbackQuery):
    url = callback.message.reply_to_message.text.strip()
    action = callback.data
    
    status_msg = await callback.message.edit_text("⏳ Идет скачивание...")
    user_id = callback.from_user.id
    
    if action == "dl_video":
        output_path = f"downloads/{user_id}_video.mp4"
        ydl_opts = {'format': 'mp4', 'outtmpl': output_path, 'quiet': True}
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
            if os.path.exists(output_path):
                await callback.message.answer_video(FSInputFile(output_path), caption="✅ Ваше видео готово!")
                stats_counter['videos'] += 1
                os.remove(output_path)
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ Ошибка при скачивании видео.")
        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка: {str(e)}")
            
    elif action == "dl_audio":
        output_path = f"downloads/{user_id}_audio.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
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
                await callback.message.answer_audio(FSInputFile(output_path), caption="✅ Ваш трек в формате MP3!")
                stats_counter['audio'] += 1
                os.remove(output_path)
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ Ошибка при скачивании аудио.")
        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка: {str(e)}")
            
    await callback.answer()

# Превращение картинки в Стикер
@dp.message(F.photo)
async def photo_to_sticker_handler(message: types.Message):
    register_user(message.from_user.id)
    status_msg = await message.answer("🎨 Превращаю картинку в стикер...")
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    
    input_path = f"downloads/{message.from_user.id}_img.jpg"
    output_sticker = f"downloads/{message.from_user.id}_sticker.webp"
    
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
        await status_msg.edit_text("❌ Не удалось сделать стикер.")

# Превращение видео в кружочек или вызов действий для видео
@dp.message(F.video | F.document)
async def media_file_handler(message: types.Message):
    register_user(message.from_user.id)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🔄 Сделать кружочек", callback_data="convert_note"),
            types.InlineKeyboardButton(text="🎵 Извлечь MP3", callback_data="convert_mp3")
        ]
    ])
    await message.answer("🎬 Что сделать с этим видео?", reply_markup=kb, reply_to_message_id=message.message_id)

@dp.callback_query(F.data.in_({"convert_note", "convert_mp3"}))
async def process_media_file(callback: types.CallbackQuery):
    msg = callback.message.reply_to_message
    file_id = msg.video.file_id if msg.video else msg.document.file_id
    user_id = callback.from_user.id
    
    status_msg = await callback.message.edit_text("⏳ Обрабатываю файл...")
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
            await status_msg.edit_text("❌ Не удалось сделать кружочек.")
            
    elif callback.data == "convert_mp3":
        output_mp3 = f"downloads/{user_id}_audio.mp3"
        ffmpeg_cmd = f'ffmpeg -y -i {input_file} -vn -acodec libmp3lame -q:a 2 {output_mp3}'
        process = await asyncio.create_subprocess_shell(ffmpeg_cmd)
        await process.communicate()
        
        if os.path.exists(output_mp3):
            await callback.message.answer_audio(FSInputFile(output_mp3), caption="🎵 Аудио из видео")
            stats_counter['audio'] += 1
            await status_msg.delete()
            os.remove(output_mp3)
        else:
            await status_msg.edit_text("❌ Не удалось извлечь аудио.")

    if os.path.exists(input_file):
        os.remove(input_file)
    await callback.answer()

# Озвучка /say
@dp.message(F.text.startswith("/say"))
async def text_to_speech_handler(message: types.Message):
    register_user(message.from_user.id)
    text = message.text.replace("/say", "").strip()
    if not text:
        return await message.answer("⚠️ Напиши текст после команды, например: `/say Привет`", parse_mode="Markdown")
    output_audio = f"downloads/{message.from_user.id}_audio.ogg"
    
    lang = user_languages.get(message.from_user.id, "ru")
    tts_lang = "ru" if lang == "ru" else ("en" if lang == "en" else "ru")
    
    gTTS(text=text, lang=tts_lang).save(output_audio)
    await message.answer_voice(FSInputFile(output_audio))
    os.remove(output_audio)

async def main():
    await set_main_menu(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
