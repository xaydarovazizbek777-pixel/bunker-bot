import os
import time
import random
import string
import sqlite3
import threading
from flask import Flask
import telebot
from telebot import types

TOKEN = "8963766433:AAFX8f3AW0IuHq_BDBVPhgU4U3wcMAhjGPA"
bot = telebot.TeleBot(TOKEN)

# --- ID АДМИНИСТРАТОРОВ ---
ADMIN_IDS = [5435444673]

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bunker Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

CHANNEL_URL = "https://t.me/bunker_game_official"

# --- ИНИЦИАЛИЗА БАЗЫ ДАННЫХ SQLITE ---
def init_db():
    conn = sqlite3.connect("bunker.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            lang TEXT DEFAULT 'ru',
            coins INTEGER DEFAULT 100,
            vip INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect("bunker.db", check_same_thread=False)

def get_user_info(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT lang, coins, vip FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, lang, coins, vip) VALUES (?, 'ru', 100, 0)", (user_id,))
        conn.commit()
        info = {"lang": "ru", "coins": 100, "vip": False}
    else:
        info = {"lang": row[0], "coins": row[1], "vip": bool(row[2])}
    conn.close()
    return info

def update_user(user_id, lang=None, coins=None, vip=None):
    conn = get_db()
    cursor = conn.cursor()
    if lang is not None:
        cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
    if coins is not None:
        cursor.execute("UPDATE users SET coins = ? WHERE user_id = ?", (coins, user_id))
    if vip is not None:
        cursor.execute("UPDATE users SET vip = ? WHERE user_id = ?", (int(vip), user_id))
    conn.commit()
    conn.close()

# --- ПЕРЕМЕННЫЕ ИГР И СОСТОЯНИЙ ---
active_games = {}   # game_code: { "host_id": ..., "players": [...], "alive": [...], "bunker_capacity": 2, "round": 1, "status": "lobby", "votes": {}, "cards": {}, "used_abilities": {} }
user_to_game = {}   # user_id: game_code
awaiting_code = {}  # user_id: True
broadcasting = {}   # admin_id: True

# --- ХАРАКТЕРИСТИКИ ---
PROFESSIONS = ["💼 Врач-хирург", "💼 Инженер-механик", "💼 Агроном", "💼 Строитель", "💼 Ученый-физик", "💼 Повар", "💼 Электрик", "💼 Военный", "💼 Программист", "💼 Психолог"]
HEALTH_LIST = ["🏥 Абсолютно здоров", "🏥 Легкая аллергия", "🏥 Близорукость (-2)", "🏥 Астма (есть ингалятор)", "🏥 Бессонница", "🏥 Диабет I типа"]
HOBBIES = ["🎨 Выживальщик / Туризм", "🎨 Стрельба из лука", "🎨 Боевые искусства", "🎨 Радиолюбитель", "🎨 Огородничество", "🎨 Плотничество"]
PHOBIAS = ["👁 Боязнь замкнутых пространств", "👁 Темнота", "👁 Высота", "👁 Пауки и насекомые", "👁 Кровь", "👁 Грязь и бактерии"]
INVENTORIES = ["🎒 Набор инструментов", "🎒 Аптечка первой помощи", "🎒 Зажигалка и фонарик", "🎒 Запас еды на 3 дня", "🎒 Рация", "🎒 Фильтр для воды"]
FERTILITY = ["🧬 Способность к размножению: Да (Здоров)", "🧬 Способность к размножению: Нет (Бесплоден)"]
FACTS = ["📌 Знает 3 иностранных языка", "📌 Имеет опыт службы в МЧС", "📌 Умеет управлять вертолетом", "📌 Бывший чемпион по боксу", "📌 Умеет готовить лекарства из трав", "📌 Нет вредных привычек"]

ABILITIES = [
    {"id": "double_vote", "name": "✌️ Двойной голос", "desc": "Твой голос при голосовании в этом раунде считается за 2!"},
    {"id": "immunity", "name": "🛡 Иммунитет", "desc": "Защищает тебя от вылета в этом раунде!"},
    {"id": "reveal_card", "name": "🔍 Шпион", "desc": "Узнать случайную карточку соперника."}
]

EVENTS = [
    "🚨 **Авария в бункере!** Вышла из строя система фильтрации воздуха.",
    "⚠️ **Угроза заражения!** Один из фильтров воды забился.",
    "⚡ **Сбой электросети!** Свет погас на 30 минут...",
    "☄️ **Метеоритный дождь!** Нарушена внешняя обшивка бункера."
]

TEXTS = {
    "ru": {
        "welcome": (
            "👋 **Добро пожаловать в официальную игру «Бункер»!** ☣️\n\n"
            "Выживай, доказывай свою важность и исключай слабых участников!\n\n"
            "📢 **Следи за новостями и обновлениями в нашем канале!**\n"
            "🎮 Создавай комнаты, делись кодом с друзьями и играйте вместе!"
        ),
        "rules": (
            "📖 **Правила игры «Бункер»:**\n\n"
            "1️⃣ На Земле произошла катастрофа. Спастись можно только в Бункере.\n"
            "2️⃣ Количество мест в бункере ограничено! Выживут не все.\n"
            "3️⃣ Игроки получают карточки персонажей (профессия, здоровье, возраст, факты и способности).\n"
            "4️⃣ В каждом раунде вы обсуждаете, кто полезнее для восстановления цивилизации.\n"
            "5️⃣ В конце каждого раунда проходит голосование. Игрок с большинством голосов **выбывает**.\n"
            "6️⃣ Игра идет до тех пор, пока количество оставшихся не сравняется с вместимостью бункера!"
        ),
        "add_to_chat": "➕ Добавить в группу 👥",
        "channel_btn": "📢 Канал обновлений",
        "create_game": "🎮 Создать игру",
        "join_game": "🔗 Подключиться по коду",
        "profile": "👤 Профиль & Монеты",
        "shop": "💎 VIP Магазин (20 ⭐️)",
    },
    "uz": {
        "welcome": (
            "👋 **«Bunker» rasmiy o'yiniga xush kelibsiz!** ☣️\n\n"
            "Tirik qoling, o'z muhimligingizni isbotlang va boshqalarni chiqarib yuboring!\n\n"
            "📢 **Yangiliklar va yangilanishlarni kanalimizda kuzatib boring!**\n"
            "🎮 Xonalar yarating, do'stlaringizga kodni yuboring va birgalikda o'ynang!"
        ),
        "rules": (
            "📖 **«Bunker» o'yini qoidalari:**\n\n"
            "1️⃣ YERda felokat yuz berdi. Faqat Bunkerdagina saqlanib qolish mumkin.\n"
            "2️⃣ Bunkerdagi joylar cheklangan!\n"
            "3️⃣ Har bir raundda kim jamiyat uchun foydaliroq ekanini muhokama qilasiz.\n"
            "4️⃣ Ovoz berish orqali eng kam foydali o'yinchi chiqib ketadi."
        ),
        "add_to_chat": "➕ Guruhga qo'shish 👥",
        "channel_btn": "📢 Yangiliklar kanali",
        "create_game": "🎮 O'yin yaratish",
        "join_game": "🔗 Kod orqali qo'shilish",
        "profile": "👤 Profil & Tangalar",
        "shop": "💎 VIP Do'kon (20 ⭐️)",
    },
    "en": {
        "welcome": (
            "👋 **Welcome to the official «Bunker» game!** ☣️\n\n"
            "Survive, prove your importance, and eliminate weak players!\n\n"
            "📢 **Follow news and updates in our official channel!**\n"
            "🎮 Create rooms, share the code with friends, and play together!"
        ),
        "rules": (
            "📖 **«Bunker» Game Rules:**\n\n"
            "1️⃣ A catastrophe happened on Earth. Only the Bunker can save you.\n"
            "2️⃣ Seats are limited! Discuss and survive each round.\n"
            "3️⃣ Vote to eliminate the least useful player until the bunker is filled!"
        ),
        "add_to_chat": "➕ Add to Group 👥",
        "channel_btn": "📢 Updates Channel",
        "create_game": "🎮 Create Game",
        "join_game": "🔗 Join via Code",
        "profile": "👤 Profile & Coins",
        "shop": "💎 VIP Shop (20 ⭐️)",
    }
}

def generate_game_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def generate_random_card():
    gender = random.choice(["👨 Мужчина", "👩 Женщина"])
    age = random.randint(18, 65)
    return {
        "gender_age": f"{gender}, {age} лет",
        "profession": random.choice(PROFESSIONS),
        "health": random.choice(HEALTH_LIST),
        "hobby": random.choice(HOBBIES),
        "phobia": random.choice(PHOBIAS),
        "inventory": random.choice(INVENTORIES),
        "fertility": random.choice(FERTILITY),
        "fact": random.choice(FACTS),
        "ability": random.choice(ABILITIES)
    }

# --- СЛЭШ-КОМАНДЫ ---
@bot.message_handler(commands=['start'])
def cmd_start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
        types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="set_lang_uz"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")
    )
    bot.send_message(message.chat.id, "🌐 Выберите язык / Tilni tanlang / Choose language:", reply_markup=markup)

@bot.message_handler(commands=['rules'])
def cmd_rules(message):
    info = get_user_info(message.from_user.id)
    lang = info["lang"]
    bot.send_message(message.chat.id, TEXTS[lang]["rules"], parse_mode="Markdown")

@bot.message_handler(commands=['create'])
def cmd_create_slash(message):
    cmd_create_game(message)

@bot.message_handler(commands=['profile'])
def cmd_profile_slash(message):
    cmd_profile(message)

@bot.message_handler(commands=['shop'])
def cmd_shop_slash(message):
    cmd_shop(message)

# --- АДМИН ПАНЕЛЬ ---
@bot.message_handler(commands=['admin'])
def cmd_admin(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"))
    markup.add(types.InlineKeyboardButton("📢 Массовая рассылка", callback_data="admin_broadcast"))
    
    bot.send_message(message.chat.id, "👑 **Панель Администратора**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def cb_admin(call):
    if call.from_user.id not in ADMIN_IDS:
        return

    if call.data == "admin_stats":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE vip = 1")
        total_vips = cursor.fetchone()[0]
        conn.close()

        bot.send_message(
            call.message.chat.id,
            f"📊 **Статистика бота:**\n\n"
            f"👤 Всего пользователей в БД: **{total_users}**\n"
            f"👑 Всего VIP-игроков: **{total_vips}**\n"
            f"🎮 Активных игр прямо сейчас: **{len(active_games)}**",
            parse_mode="Markdown"
        )
    elif call.data == "admin_broadcast":
        broadcasting[call.from_user.id] = True
        bot.send_message(call.message.chat.id, "📝 Введи текст сообщения для рассылки всем пользователям:")

@bot.message_handler(func=lambda m: broadcasting.get(m.from_user.id, False))
def process_broadcast(message):
    broadcasting[message.from_user.id] = False
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()

    count = 0
    bot.send_message(message.chat.id, "🚀 Начинаем рассылку...")
    for u in users:
        try:
            bot.send_message(u[0], message.text, parse_mode="Markdown")
            count += 1
            time.sleep(0.05)
        except Exception:
            pass

    bot.send_message(message.chat.id, f"✅ Рассылка завершена! Успешно отправлено: **{count}** пользователям.")

# --- СМЕНА ЯЗЫКА И МЕНЮ ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("set_lang_"))
def cb_lang(call):
    lang = call.data.split("_")[-1]
    update_user(call.from_user.id, lang=lang)
    bot.answer_callback_query(call.id, "OK! 👌")
    show_main_menu(call.message.chat.id, call.from_user.id, edit_message_id=call.message.message_id)

def show_main_menu(chat_id, user_id, edit_message_id=None):
    info = get_user_info(user_id)
    lang = info["lang"]
    bot_username = bot.get_me().username
    
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    reply_markup.add(
        types.KeyboardButton(TEXTS[lang]["create_game"]),
        types.KeyboardButton(TEXTS[lang]["join_game"])
    )
    reply_markup.add(
        types.KeyboardButton(TEXTS[lang]["profile"]),
        types.KeyboardButton(TEXTS[lang]["shop"])
    )
    
    inline_markup = types.InlineKeyboardMarkup(row_width=1)
    inline_markup.add(
        types.InlineKeyboardButton(TEXTS[lang]["channel_btn"], url=CHANNEL_URL),
        types.InlineKeyboardButton(TEXTS[lang]["add_to_chat"], url=f"https://t.me/{bot_username}?startgroup=true")
    )

    if edit_message_id:
        try:
            bot.edit_message_text(
                TEXTS[lang]["welcome"],
                chat_id=chat_id,
                message_id=edit_message_id,
                parse_mode="Markdown",
                reply_markup=inline_markup
            )
            bot.send_message(chat_id, "👇 Выберите действие:", reply_markup=reply_markup)
        except Exception:
            bot.send_message(chat_id, TEXTS[lang]["welcome"], reply_markup=reply_markup, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, TEXTS[lang]["welcome"], reply_markup=reply_markup, parse_mode="Markdown")

# --- СОЗДАНИЕ И ПОДКЛЮЧЕНИЕ К ИГРЕ ---
@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["create_game"], TEXTS["uz"]["create_game"], TEXTS["en"]["create_game"]])
def cmd_create_game(message):
    user = message.from_user
    code = generate_game_code()
    
    active_games[code] = {
        "host_id": user.id,
        "players": [user],
        "alive": [user],
        "bunker_capacity": 1,
        "round": 1,
        "status": "lobby",
        "votes": {},
        "cards": {},
        "used_abilities": {}
    }
    user_to_game[user.id] = code
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Начать игру", callback_data=f"start_game_{code}"))
    
    bot.send_message(
        message.chat.id,
        f"🎮 **Комната создана!**\n\n🔑 Код комнаты: `{code}`\n\nОтправь этот код друзьям!\n\n👥 **Участники в лобби (1):**\n• {user.first_name}",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["join_game"], TEXTS["uz"]["join_game"], TEXTS["en"]["join_game"]])
def cmd_join_prompt(message):
    awaiting_code[message.from_user.id] = True
    bot.send_message(message.chat.id, "🔑 **Введи 6-значный код комнаты:**")

@bot.message_handler(func=lambda m: awaiting_code.get(m.from_user.id, False))
def process_join_code(message):
    code = message.text.strip().upper()
    user = message.from_user
    
    if code not in active_games or active_games[code]["status"] != "lobby":
        bot.reply_to(message, "❌ Игра не найдена или уже началась! Проверь код.")
        return
    
    game = active_games[code]
    if any(p.id == user.id for p in game["players"]):
        bot.reply_to(message, "⚠️ Вы уже находитесь в этой комнате!")
        awaiting_code[user.id] = False
        return

    game["players"].append(user)
    game["alive"].append(user)
    user_to_game[user.id] = code
    awaiting_code[user.id] = False
    
    bot.send_message(message.chat.id, f"✅ Вы успешно вошли в комнату `{code}`!", parse_mode="Markdown")
    
    players_list = "\n".join([f"• {p.first_name}" for p in game["players"]])
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Начать игру", callback_data=f"start_game_{code}"))
    
    bot.send_message(
        game["host_id"],
        f"🔔 **Новый игрок зашел!**\n\n🔑 Код: `{code}`\n\n👥 **Участники ({len(game['players'])}):**\n{players_list}",
        parse_mode="Markdown",
        reply_markup=markup
    )

# --- ИГРОВОЙ ПРОЦЕСС ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("start_game_"))
def cb_start_game(call):
    code = call.data.split("_")[-1]
    game = active_games.get(code)
    
    if not game:
        bot.answer_callback_query(call.id, "Игра не найдена.")
        return
        
    if call.from_user.id != game["host_id"]:
        bot.answer_callback_query(call.id, "Только создатель комнаты может начать игру!", show_alert=True)
        return

    game["status"] = "in_progress"
    total_players = len(game["players"])
    game["bunker_capacity"] = max(1, total_players // 2)
    
    for player in game["players"]:
        card = generate_random_card()
        game["cards"][player.id] = card

    start_new_round(code)

def start_new_round(code):
    game = active_games.get(code)
    if not game:
        return
        
    event = random.choice(EVENTS)
    game["votes"] = {}
    
    msg_text = (
        f"🔄 **РАУНД {game['round']}**\n\n"
        f"{event}\n\n"
        f"👥 Выжившие: **{len(game['alive'])}**\n"
        f"🏛 Мест в бункере: **{game['bunker_capacity']}**\n\n"
        f"⏳ Обсуждение (60 секунд)... Доказывайте свою ценность!"
    )
    
    game_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    game_markup.add(types.KeyboardButton("🎴 Моя карта"), types.KeyboardButton("⚡ Использовать способность"))

    for player in game["alive"]:
        try:
            bot.send_message(player.id, msg_text, parse_mode="Markdown", reply_markup=game_markup)
            send_player_card(player.id, game["cards"][player.id])
        except Exception:
            pass

    threading.Thread(target=run_discussion_timer, args=(code, 60)).start()

def send_player_card(user_id, card):
    card_text = (
        "📋 **Твоя карточка выжившего:**\n\n"
        + "👤 " + card['gender_age'] + "\n"
        + card['profession'] + "\n"
        + card['health'] + "\n"
        + card['hobby'] + "\n"
        + card['phobia'] + "\n"
        + card['inventory'] + "\n"
        + card['fertility'] + "\n"
        + card['fact'] + "\n\n"
        + "⚡ **Особая фишка:** " + card['ability']['name'] + "\n"
        + "📝 _" + card['ability']['desc'] + "_"
    )
    bot.send_message(user_id, card_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🎴 Моя карта")
def show_my_card(message):
    user_id = message.from_user.id
    code = user_to_game.get(user_id)
    game = active_games.get(code)
    if game and user_id in game["cards"]:
        send_player_card(user_id, game["cards"][user_id])

@bot.message_handler(func=lambda m: m.text == "⚡ Использовать способность")
def use_ability(message):
    user_id = message.from_user.id
    code = user_to_game.get(user_id)
    game = active_games.get(code)
    
    if not game or user_id not in game["cards"]:
        return

    if user_id in game["used_abilities"]:
        bot.reply_to(message, "⚠️ Вы уже использовали свою способность!")
        return

    ability = game["cards"][user_id]["ability"]
    
    if ability["id"] == "reveal_card":
        other_players = [p for p in game["alive"] if p.id != user_id]
        if other_players:
            target = random.choice(other_players)
            target_card = game["cards"][target.id]
            bot.send_message(
                user_id,
                f"🔍 **ШПИОНАЖ:** Карточка игрока **{target.first_name}**:\n\n"
                f"{target_card['profession']}\n{target_card['health']}\n{target_card['fact']}",
                parse_mode="Markdown"
            )
            game["used_abilities"][user_id] = ability["id"]
        else:
            bot.reply_to(message, "Нет других игроков для проверки!")
            return

    elif ability["id"] in ["double_vote", "immunity"]:
        game["used_abilities"][user_id] = ability["id"]
        bot.reply_to(message, f"✅ Вы активировали фишку: **{ability['name']}**!")

    for p in game["alive"]:
        if p.id != user_id:
            bot.send_message(p.id, f"💥 **{message.from_user.first_name}** активировал фишку: **{ability['name']}**!")

def run_discussion_timer(code, seconds):
    time.sleep(seconds)
    if code in active_games:
        start_voting_phase(code)

def start_voting_phase(code):
    game = active_games.get(code)
    if not game:
        return
        
    markup = types.InlineKeyboardMarkup()
    for player in game["alive"]:
        markup.add(types.InlineKeyboardButton(f"❌ Исключить {player.first_name}", callback_data=f"vote_{code}_{player.id}"))
    
    for player in game["alive"]:
        bot.send_message(player.id, "🗳 **Время на обсуждение вышло! Начинаем голосование!** 🔥\nВыберите игрока для исключения:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vote_"))
def cb_vote(call):
    parts = call.data.split("_")
    code = parts[1]
    target_id = int(parts[2])
    voter_id = call.from_user.id
    
    game = active_games.get(code)
    if not game:
        bot.answer_callback_query(call.id, "Игра завершена.")
        return
        
    game["votes"][voter_id] = target_id
    bot.answer_callback_query(call.id, "Ваш голос принят! 🗳")
    
    if len(game["votes"]) >= len(game["alive"]):
        finish_voting(code)

def finish_voting(code):
    game = active_games.get(code)
    if not game:
        return
        
    vote_counts = {}
    for voter, target in game["votes"].items():
        weight = 2 if game["used_abilities"].get(voter) == "double_vote" else 1
        vote_counts[target] = vote_counts.get(target, 0) + weight
        
    kicked_id = max(vote_counts, key=vote_counts.get) if vote_counts else None
    
    if kicked_id and game["used_abilities"].get(kicked_id) == "immunity":
        for p in game["alive"]:
            bot.send_message(p.id, "🛡 **Игрок с наибольшим количеством голосов защитился ИММУНИТЕТОМ!** Никто не вылетает.")
    elif kicked_id:
        kicked_player = next((pl for pl in game["alive"] if pl.id == kicked_id), None)
        if kicked_player:
            game["alive"].remove(kicked_player)
            for p in game["players"]:
                bot.send_message(p.id, f"❌ **Игрок {kicked_player.first_name} исключен из бункера!**")

    if len(game["alive"]) <= game["bunker_capacity"]:
        finish_game(code)
    else:
        game["round"] += 1
        time.sleep(3)
        start_new_round(code)

def finish_game(code):
    game = active_games.get(code)
    if not game:
        return

    winners_list = "\n".join([f"🏆 {p.first_name}" for p in game["alive"]])
    
    for p in game["players"]:
        info = get_user_info(p.id)
        update_user(p.id, coins=info["coins"] + 50)
        bot.send_message(
            p.id,
            f"🎉 **ИГРА ЗАВЕРШЕНА!** ☣️\n\n Выжившие, вошедшие в бункер:\n{winners_list}\n\n🪙 Всем участникам начислено +50 монет!",
            parse_mode="Markdown"
        )
    
    del active_games[code]

# --- ПРОФИЛЬ И VIP МАГАЗИН ---
@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["profile"], TEXTS["uz"]["profile"], TEXTS["en"]["profile"]])
def cmd_profile(message):
    info = get_user_info(message.from_user.id)
    vip_status = "👑 VIP Игрок" if info["vip"] else "👤 Обычный игрок"
    bot.send_message(
        message.chat.id,
        f"👤 **Профиль игрока**\n\n🆔 ID: `{message.from_user.id}`\nСтатус: {vip_status}\n🪙 Монеты: **{info['coins']}**",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["shop"], TEXTS["uz"]["shop"], TEXTS["en"]["shop"]])
def cmd_shop(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⭐ Купить VIP за 20 Stars", callback_data="buy_vip_stars"))
    
    bot.send_message(
        message.chat.id,
        "💎 **VIP Магазин «Бункер»**\n\n"
        "👑 **VIP-Статус дает:**\n"
        "• Выделение ника короной 👑\n"
        "• На старт +500 монет 🪙\n"
        "• Возможность 1 раз за игру бесплатно пересдать карту!\n\n"
        "💳 Стоимость: **20 Telegram Stars ⭐️**",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "buy_vip_stars")
def buy_vip_stars(call):
    prices = [types.LabeledPrice(label="VIP Статус Бункер", amount=20)]
    bot.send_invoice(
        call.message.chat.id,
        title="👑 VIP-Статус Бункер",
        description="Получи VIP статус, золотую корону и 500 монет!",
        invoice_payload="vip_buy_payload",
        provider_token="",
        currency="XTR",
        prices=prices
    )

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def process_payment(message):
    info = get_user_info(message.from_user.id)
    update_user(message.from_user.id, vip=True, coins=info["coins"] + 500)
    bot.send_message(message.chat.id, "🎉 **Поздравляем! Вы успешно купили VIP за 20 Stars!** 👑\nВам также начислено 500 монет!")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Бот и веб-сервер успешно запущены!")
    bot.infinity_polling()
