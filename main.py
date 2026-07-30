import random
import telebot
from telebot import types

TOKEN = "8963766433:AAFX8f3AW0IuHq_BDBVPhgU4U3wcMAhjGPA"
bot = telebot.TeleBot(TOKEN)

# Хранилища данных
private_rooms = {}  # Игра по коду в ЛС: { "4829": {"host": id, "players": [id1, id2]} }
group_games = {}    # Игра в группах: { chat_id: {"host": id, "players": [id1, id2]} }
user_states = {}    # Состояния для ввода кода

# --- 🎲 ФУНКЦИЯ ГЕНЕРАЦИИ ПЕРСОНАЖА ---
def generate_survivor_card():
    professions = ["Врач", "Инженер", "Повар", "Строитель", "Ученый", "Программист", "Военный", "Агроном", "Электрик"]
    health_status = ["Идеально здоров", "Астма", "Легкая хромота", "Аллергия", "Зрение 100%", "Бессонница"]
    hobbies = ["Охота", "Кулинария", "Ремонт техники", "Спорт", "Чтение книг", "Ботаника", "Стрельба"]
    
    prof = random.choice(professions)
    age = random.randint(18, 65)
    gender = random.choice(["Мужчина", "Женщина"])
    health = random.choice(health_status)
    hobby = random.choice(hobbies)
    
    card = (
        f"👤 **Карта Выжившего**\n\n"
        f"🔹 **Пол:** {gender}\n"
        f"🔹 **Возраст:** {age} лет\n"
        f"🔹 **Профессия:** {prof}\n"
        f"🔹 **Здоровье:** {health}\n"
        f"🔹 **Хобби:** {hobby}"
    )
    return card


# ==========================================
# 🏠 1. ЛИЧНЫЕ СООБЩЕНИЯ (ИГРА ПО КОДУ)
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type == 'private':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("➕ Создать комнату (по коду)")
        btn2 = types.KeyboardButton("🚪 Войти по коду")
        btn3 = types.KeyboardButton("🎲 Получить карту выжившего")
        markup.add(btn1, btn2)
        markup.add(btn3)

        bot.send_message(
            message.chat.id,
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            f"Добро пожаловать в систему выживания **«Бункер»** ☣️\n\n"
            f"• Жми **«Создать комнату»**, чтобы играть с друзьями по коду.\n"
            f"• Или **добавь бота в групповой чат** и напиши там `/newgame`!",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        bot.reply_to(message, "Чтобы начать игру в этом чате, напишите команду /newgame 🚀")


@bot.message_handler(func=lambda msg: msg.text == "🎲 Получить карту выжившего")
def solo_card(message):
    card = generate_survivor_card()
    bot.send_message(message.chat.id, card, parse_mode="Markdown")


@bot.message_handler(func=lambda msg: msg.text == "➕ Создать комнату (по коду)")
def create_room(message):
    user_id = message.from_user.id
    code = str(random.randint(1000, 9999))
    while code in private_rooms:
        code = str(random.randint(1000, 9999))

    private_rooms[code] = {"host": user_id, "players": [user_id]}

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Начать игру (Хост)", callback_data=f"privstart_{code}"))

    bot.send_message(
        message.chat.id,
        f"🏰 **Комната #{code} создана!**\n\nПередай этот код друзьям.\n👥 Игроков в лобби: 1",
        reply_markup=markup,
        parse_mode="Markdown"
    )


@bot.message_handler(func=lambda msg: msg.text == "🚪 Войти по коду")
def join_request(message):
    user_states[message.from_user.id] = "waiting_for_code"
    bot.send_message(message.chat.id, "🔢 Введи 4-значный код комнаты:")


@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "waiting_for_code")
def process_code(message):
    code = message.text.strip()
    user_id = message.from_user.id

    if code in private_rooms:
        if user_id not in private_rooms[code]["players"]:
            private_rooms[code]["players"].append(user_id)
            user_states[user_id] = None
            
            bot.send_message(message.chat.id, f"✅ Ты успешно вошел в комнату **#{code}**!", parse_mode="Markdown")
            
            host_id = private_rooms[code]["host"]
            count = len(private_rooms[code]["players"])
            bot.send_message(host_id, f"👤 Новый игрок присоединился!\n👥 Всего участников в лобби: {count}")
        else:
            bot.send_message(message.chat.id, "Ты уже в этой комнате!")
    else:
        bot.send_message(message.chat.id, "❌ Комната не найдена. Попробуй ещё раз:")


@bot.callback_query_handler(func=lambda call: call.data.startswith("privstart_"))
def start_private_game(call):
    code = call.data.split("_")[1]
    room = private_rooms.get(code)

    if not room or call.from_user.id != room["host"]:
        bot.answer_callback_query(call.id, "Только хост может начать игру!", show_alert=True)
        return

    for player_id in room["players"]:
        card = generate_survivor_card()
        bot.send_message(player_id, f"🎮 **ИГРА НАЧАЛАСЬ!**\n\n{card}", parse_mode="Markdown")

    bot.edit_message_text(f"🏁 Игра #{code} запущена! Карты рассланы.", chat_id=call.message.chat.id, message_id=call.message.message_id)


# ==========================================
# 👥 2. ГРУППОВЫЕ ЧАТЫ (КОМАНДА /newgame)
# ==========================================

@bot.message_handler(commands=['newgame'])
def create_group_game(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "⚠️ Команду /newgame нужно использовать в групповом чате с друзьями!")
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    group_games[chat_id] = {
        "host": user_id,
        "players": [user_id]
    }

    markup = types.InlineKeyboardMarkup()
    btn_join = types.InlineKeyboardButton("✋ Присоединиться", callback_data="grp_join")
    btn_start = types.InlineKeyboardButton("🚀 Начать игру (Хост)", callback_data="grp_start")
    markup.add(btn_join)
    markup.add(btn_start)

    bot.send_message(
        chat_id,
        f"☣️ **Инициализация игры «Бункер» в чате!**\n\n"
        f"Организатор: @{message.from_user.username or message.from_user.first_name}\n"
        f"👥 Записались: 1 чел.\n\n"
        f"⚠️ *Жмите кнопку ниже! (Перед входом убедитесь, что вы нажали /start у бота в ЛС)*",
        reply_markup=markup,
        parse_mode="Markdown"
    )


@bot.callback_query_handler(func=lambda call: call.data in ["grp_join", "grp_start"])
def handle_group_game(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    game = group_games.get(chat_id)

    if not game:
        bot.answer_callback_query(call.id, "Игра не найдена. Напишите /newgame!", show_alert=True)
        return

    # Нажали "Присоединиться"
    if call.data == "grp_join":
        if user_id not in game["players"]:
            game["players"].append(user_id)
            bot.answer_callback_query(call.id, "Ты успешно записан на игру!")

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✋ Присоединиться", callback_data="grp_join"))
            markup.add(types.InlineKeyboardButton("🚀 Начать игру (Хост)", callback_data="grp_start"))

            bot.edit_message_text(
                f"☣️ **Инициализация игры «Бункер»!**\n\n👥 Записалось участников: {len(game['players'])}",
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(call.id, "Ты уже в игре!")

    # Нажали "Начать игру"
    elif call.data == "grp_start":
        if user_id != game["host"]:
            bot.answer_callback_query(call.id, "Только хост может запустить игру!", show_alert=True)
            return

        bot.answer_callback_query(call.id, "Запускаем игру...")

        # Рассылка карт всем записавшимся
        for p_id in game["players"]:
            try:
                card = generate_survivor_card()
                bot.send_message(p_id, f"🎮 **ИГРА В ЧАТЕ НАЧАЛАСЬ!**\n\nВот твоя секретная карта:\n\n{card}", parse_mode="Markdown")
            except:
                pass # Если игрок не написал /start в ЛС заранее

        bot.send_message(
            chat_id, 
            "🌋 **КАТАСТРОФА НАЧАЛАСЬ!**\n\nВсем участникам отправлены карты в ЛС 📩. Открывайте свои профессии и начинайте дискуссию!",
            parse_mode="Markdown"
        )


# Запуск
print("Бот запущен и готов к работе в ЛС и Группах!")
# Показ характеристики игрока по команде /mycard
@bot.message_handler(commands=['mycard'])
def show_my_card(message):
    user_id = message.from_user.id
    if user_id in players:
        card = players[user_id]['card']
        text = "🪪 **Твоя карточка:**\n\n"
        for key, value in card.items():
            text += f"🔹 **{key}:** {value}\n"
        bot.send_message(user_id, text, parse_mode="Markdown")
    else:
        bot.send_message(user_id, "Ты не в игре!")

bot.polling(none_stop=True)
