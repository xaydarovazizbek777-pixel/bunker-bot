import os
import time
import random
import string
import sqlite3
import threading
from datetime import datetime, timedelta
from flask import Flask
import telebot
from telebot import types

# --- НАСТРОЙКИ БОТА ---
TOKEN = "8963766433:AAFX8f3AW0IuHq_BDBVPhgU4U3wcMAhjGPA"
bot = telebot.TeleBot(TOKEN)
BOT_USERNAME = "Bunker_live_bot"

# --- ID АДМИНИСТРАТОРОВ ---
ADMIN_IDS = [5435444673]

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER / REPLIT ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bunker Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- РЕГИСТРАЦИЯ МЕНЮ КОМАНД ПО СЛЕШУ (/) ---
def setup_bot_commands():
    commands = [
        types.BotCommand("start", "🚀 Главное меню / Запуск"),
        types.BotCommand("newgame", "🎮 Создать новую игру"),
        types.BotCommand("mycard", "🎴 Посмотреть свою карту (в ЛС)"),
        types.BotCommand("profile", "👤 Профиль и статистика"),
        types.BotCommand("top", "🏆 Таблица лидеров (Топ-10)"),
        types.BotCommand("lang", "🌐 Сменить язык / Language"),
        types.BotCommand("rules", "📖 Правила игры")
    ]
    try:
        bot.set_my_commands(commands)
        print("✅ Меню команд (/) успешно установлено!")
    except Exception as e:
        print(f"⚠️ Ошибка установки меню команд: {e}")

# --- ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("bunker.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT 'Выживший',
            lang TEXT DEFAULT 'ru',
            coins INTEGER DEFAULT 100,
            vip INTEGER DEFAULT 0,
            rating INTEGER DEFAULT 1000,
            games_played INTEGER DEFAULT 0,
            games_won INTEGER DEFAULT 0,
            last_bonus TEXT DEFAULT NULL,
            referrer_id INTEGER DEFAULT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect("bunker.db", check_same_thread=False)

def get_user_info(user_id, username="Выживший"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT lang, coins, vip, rating, games_played, games_won, last_bonus FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute(
            "INSERT INTO users (user_id, username, lang, coins, vip, rating, games_played, games_won) VALUES (?, ?, 'ru', 100, 0, 1000, 0, 0)",
            (user_id, username)
        )
        conn.commit()
        info = {"lang": "ru", "coins": 100, "vip": False, "rating": 1000, "played": 0, "won": 0, "last_bonus": None}
    else:
        cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        conn.commit()
        info = {
            "lang": row[0], "coins": row[1], "vip": bool(row[2]),
            "rating": row[3], "played": row[4], "won": row[5], "last_bonus": row[6]
        }
    conn.close()
    return info

def set_user_language(user_id, lang):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()

def register_user_with_ref(user_id, username="Выживший", referrer_id=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute(
            "INSERT INTO users (user_id, username, lang, coins, vip, referrer_id) VALUES (?, ?, 'ru', 100, 0, ?)",
            (user_id, username, referrer_id)
        )
        conn.commit()
        if referrer_id and referrer_id != user_id:
            cursor.execute("UPDATE users SET coins = coins + 100 WHERE user_id = ?", (referrer_id,))
            conn.commit()
            try:
                bot.send_message(referrer_id, "🎉 По вашей реферальной ссылке зарегистрировался новый игрок! Вам зачислено **+100 монет** 🪙")
            except Exception:
                pass
    conn.close()

def update_user_stats(user_id, coins_add=0, rating_add=0, win=False):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET coins = coins + ?, rating = rating + ?, games_played = games_played + 1, games_won = games_won + ? WHERE user_id = ?",
        (coins_add, rating_add, 1 if win else 0, user_id)
    )
    conn.commit()
    conn.close()

# --- ЯЗЫКОВЫЕ ТЕКСТЫ ДЛЯ ЛС ---
TEXTS = {
    "ru": {
        "welcome": "👋 **Добро пожаловать в «Бункер»!** ☣️\n\nИспользуй меню ниже для управления профилем и игрой!",
        "create_game": "🎮 Создать игру",
        "join_game": "🔗 Подключиться по коду",
        "profile": "👤 Профиль",
        "shop": "💎 VIP Магазин",
        "ref": "🤝 Рефералка",
        "top": "🏆 Топ выживших",
        "daily": "🎁 Ежедневный бонус",
        "lang": "🌐 Язык / Language"
    },
    "uz": {
        "welcome": "👋 **«Bunker» o'yiniga xush kelibsiz!** ☣️\n\nProfil va o'yinni boshqarish uchun pastdagi menyudan foydalaning!",
        "create_game": "🎮 O'yin yaratish",
        "join_game": "🔗 Kod orqali kirish",
        "profile": "👤 Profil",
        "shop": "💎 VIP Do'kon",
        "ref": "🤝 Taklif qilish",
        "top": "🏆 Top o'yinchilar",
        "daily": "🎁 Kunlik bonus",
        "lang": "🌐 Язык / Language"
    },
    "en": {
        "welcome": "👋 **Welcome to «Bunker»!** ☣️\n\nUse the menu below to manage your profile and game!",
        "create_game": "🎮 Create Game",
        "join_game": "🔗 Join by Code",
        "profile": "👤 Profile",
        "shop": "💎 VIP Shop",
        "ref": "🤝 Referral",
        "top": "🏆 Leaderboard",
        "daily": "🎁 Daily Bonus",
        "lang": "🌐 Language"
    }
}

# --- AI-КАТАСТРОФЫ И СОБЫТИЯ ---
AI_CATASTROPHES = [
    "☄️ **Падение астероида «Апофис»:** Поверхность Земли выжжена, атмосфера заполнена пеплом.",
    "☣️ **Утечка вируса «X-9»:** Внешний мир заражен опасными спорами.",
    "❄️ **Ядерная зима:** Температура упала до -65°C. Пища на исходе.",
    "🤖 **Восстание ИИ:** Боевые дроны уничтожают всё живое на поверхности.",
    "🌋 **Извержение Вулкана:** Кислотные дожди разъедают всё вокруг."
]

AI_ROUND_EVENTS = [
    "🚨 **Авария в блоке Б:** Произошла разгерметизация секции!",
    "☣️ **Заражение фильтров:** Система очистки воды дает сбой.",
    "⚡ **Сбой генератора:** Напряжение упало! Нужен ремонт.",
    "🌾 **Заплесневели припасы:** Срочно требуется ревизия еды!"
]

PROFESSIONS = ["🩺 Врач-хирург", "⚙️ Инженер-механик", "🌾 Агроном", "🏗 Строитель", "⚛️ Ученый-физик", "👨‍🍳 Шеф-повар", "⚡ Электрик", "🎖 Спецназовец", "💻 Программист", "🧠 Психотерапевт"]
HEALTH_LIST = ["🩺 Абсолютно здоров", "🌸 Аллергия на пыльцу", "👓 Близорукость", "🫁 Астма", "🩸 Диабет", "👂 Отит"]
HOBBIES = ["🏕 Выживание", "🏹 Стрельба из лука", "🥊 Рукопашный бой", "📻 Радиолюбитель", "🌱 Огородник", "🗝 Локпикинг"]
PHOBIAS = ["📦 Клаустрофобия", "🌑 Никтофобия", "🏔 Акрофобия", "🕷 Арахнофобия", "🩸 Гемофобия"]
INVENTORIES = ["🧰 Набор инструментов", "🩹 Аптечка", "🔦 Фонарь и Zippo", "🥫 Сухпаек на 5 дней", "📻 Рация", "🔪 Нож"]
FERTILITY = ["🟢 Да (Здоров)", "🔥 Да (Высокая)", "🔴 Нет (Бесплоден)"]
FACTS = ["🗣 Знает 3 языка", "🚒 Опыт МЧС", "🚁 Пилот вертолета", "🥊 Чемпион по боксу", "🚭 Без вредных привычек"]
ABILITIES = [
    {"id": "double_vote", "name": "✌️ Двойной голос", "desc": "Твой голос в этом раунде считается за 2!"},
    {"id": "immunity", "name": "🛡 Иммунитет", "desc": "Защищает от вылета в этом раунде!"},
    {"id": "reveal_card", "name": "🔍 Шпион", "desc": "Узнать случайную характеристику соперника."}
]

active_games = {}   
user_to_game = {}   

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

# --- ОБРАБОТКА КОМАНД И ГЛАВНОГО МЕНЮ ЛС ---
@bot.message_handler(commands=['start'])
def cmd_start(message):
    args = message.text.split()
    referrer_id = None
    username = message.from_user.first_name or "Выживший"
    
    if len(args) > 1:
        param = args[1]
        if param.startswith("ref_"):
            try:
                referrer_id = int(param.split("_")[1])
            except ValueError:
                pass
        elif param.startswith("join_"):
            code = param.split("_")[1]
            register_user_with_ref(message.from_user.id, username)
            join_game_by_code(message, code)
            return

    register_user_with_ref(message.from_user.id, username, referrer_id)
    show_main_menu(message.chat.id, message.from_user.id)

def show_main_menu(chat_id, user_id):
    info = get_user_info(user_id)
    lang = info["lang"] if info["lang"] in TEXTS else "ru"
    t = TEXTS[lang]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton(t["create_game"]), types.KeyboardButton(t["join_game"]))
    markup.add(types.KeyboardButton(t["profile"]), types.KeyboardButton(t["top"]))
    markup.add(types.KeyboardButton(t["daily"]), types.KeyboardButton(t["shop"]))
    markup.add(types.KeyboardButton(t["ref"]), types.KeyboardButton(t["lang"]))
    
    bot.send_message(chat_id, t["welcome"], reply_markup=markup, parse_mode="Markdown")

# --- ВЫБОР ЯЗЫКА (ТОЛЬКО В ЛС) ---
@bot.message_handler(commands=['lang'])
@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["lang"], TEXTS["uz"]["lang"], TEXTS["en"]["lang"]])
def cmd_change_lang(message):
    if message.chat.type != 'private':
        return  # Не показывает настройки языка в общих чатах!

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"))
    markup.add(types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="set_lang_uz"))
    markup.add(types.InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"))
    bot.send_message(message.chat.id, "🌐 **Выберите язык интерфейса / Select language / Tilni tanlang:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_lang_"))
def cb_set_lang(call):
    lang_code = call.data.split("_")[-1]
    set_user_language(call.from_user.id, lang_code)
    bot.answer_callback_query(call.id, "Язык обновлен! / Language updated! / Til yangilandi!")
    show_main_menu(call.message.chat.id, call.from_user.id)

@bot.message_handler(commands=['rules'])
def cmd_rules(message):
    bot.send_message(
        message.chat.id,
        "📖 **Правила игры «Бункер»:**\n\n1️⃣ На Земле произошла катастрофа.\n2️⃣ У каждого игрока есть уникальная карта характеристик.\n3️⃣ Раундами через споры и голосования выбиваются самые бесполезные выжившие.\n4️⃣ Выигрывают те, кто вошёл в бункер!",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['newgame'])
def cmd_newgame_slash(message):
    handle_create_game(message)

@bot.message_handler(commands=['mycard'])
def cmd_mycard_slash(message):
    user_id = message.from_user.id
    code = user_to_game.get(user_id)
    game = active_games.get(code)
    if game and user_id in game["cards"]:
        send_player_card_private(user_id, game["cards"][user_id])
    else:
        bot.send_message(message.chat.id, "⚠️ Вы сейчас не находитесь в активной игре!")

@bot.message_handler(commands=['profile'])
@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["profile"], TEXTS["uz"]["profile"], TEXTS["en"]["profile"]])
def cmd_profile(message):
    info = get_user_info(message.from_user.id, message.from_user.first_name)
    vip_status = "👑 VIP Игрок" if info["vip"] else "👤 Обычный игрок"
    winrate = round((info["won"] / info["played"] * 100), 1) if info["played"] > 0 else 0
    
    bot.send_message(
        message.chat.id,
        f"👤 **Профиль выжившего:**\n\n🆔 ID: `{message.from_user.id}`\n✨ Статус: {vip_status}\n🪙 Монеты: **{info['coins']}**\n🏆 Рейтинг: **{info['rating']} РТС**\n\n📊 Игр: **{info['played']}** | Побед: **{info['won']}** ({winrate}%)",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['top'])
@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["top"], TEXTS["uz"]["top"], TEXTS["en"]["top"]])
def cmd_top_players(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, rating, games_won FROM users ORDER BY rating DESC LIMIT 10")
    top_users = cursor.fetchall()
    conn.close()

    text = "🏆 **ТОП-10 ВЫЖИВШИХ:**\n\n"
    for idx, user in enumerate(top_users):
        text += f"{idx+1}. **{user[0]}** — {user[1]} РТС | 🏆 {user[2]} побед\n"

    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["daily"], TEXTS["uz"]["daily"], TEXTS["en"]["daily"]])
def cmd_daily_bonus(message):
    user_id = message.from_user.id
    info = get_user_info(user_id, message.from_user.first_name)
    now = datetime.now()
    
    if info["last_bonus"]:
        last_bonus = datetime.strptime(info["last_bonus"], "%Y-%m-%d %H:%M:%S")
        if now < last_bonus + timedelta(hours=24):
            bot.send_message(message.chat.id, "⏳ Вы уже забирали бонус сегодня! Приходите завтра.")
            return

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = coins + 50, last_bonus = ? WHERE user_id = ?", (now.strftime("%Y-%m-%d %H:%M:%S"), user_id))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, "🎉 **Бонус получен:** +50 монет 🪙!")

# --- ИГРОВАЯ ЛОГИКА ---
@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["create_game"], TEXTS["uz"]["create_game"], TEXTS["en"]["create_game"]])
def handle_create_game(message):
    user = message.from_user
    code = generate_game_code()
    catastrophe = random.choice(AI_CATASTROPHES)
    
    active_games[code] = {
        "chat_id": message.chat.id,
        "host_id": user.id,
        "players": [user],
        "alive": [user],
        "bunker_capacity": 1,
        "round": 1,
        "status": "lobby",
        "catastrophe": catastrophe,
        "votes": {},
        "cards": {},
        "used_abilities": {},
        "active_immunities": [],
        "double_votes": [],
        "rerolls": {}
    }
    user_to_game[user.id] = code
    
    join_link = f"https://t.me/{BOT_USERNAME}?start=join_{code}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Войти в игру", url=join_link))
    markup.add(types.InlineKeyboardButton("🚀 Начать игру", callback_data=f"start_game_{code}"))

    bot.send_message(
        message.chat.id,
        f"🎮 **ИГРА СОЗДАНА!**\n\n🔑 Код комнаты: `{code}`\n\n🌍 **Катастрофа:**\n{catastrophe}\n\n👥 **В лобби:** {user.first_name}\n\nНажмите кнопку ниже, чтобы войти!",
        parse_mode="Markdown",
        reply_markup=markup
    )

def join_game_by_code(message, code):
    user = message.from_user

    if code not in active_games or active_games[code]["status"] != "lobby":
        bot.send_message(message.chat.id, "❌ Игра не найдена или уже началась!")
        return
    
    game = active_games[code]
    if any(p.id == user.id for p in game["players"]):
        bot.send_message(message.chat.id, "⚠️ Вы уже присоединились!")
        return

    game["players"].append(user)
    game["alive"].append(user)
    user_to_game[user.id] = code
    
    bot.send_message(message.chat.id, f"✅ Вы вошли в игру `{code}`! Ожидайте старта.", parse_mode="Markdown")
    
    players_list = ", ".join([p.first_name for p in game["players"]])
    bot.send_message(game["chat_id"], f"🔔 **{user.first_name}** вошел в игру!\n👥 **Участники ({len(game['players'])}):** {players_list}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("start_game_"))
def cb_start_game(call):
    code = call.data.split("_")[-1]
    game = active_games.get(code)
    
    if not game or call.from_user.id != game["host_id"]:
        bot.answer_callback_query(call.id, "Только создатель может начать!")
        return

    if len(game["players"]) < 3:
        bot.answer_callback_query(call.id, "⚠️ Нужно минимум 3 игрока!", show_alert=True)
        return

    game["status"] = "in_progress"
    game["bunker_capacity"] = max(1, len(game["players"]) // 2)
    
    for player in game["players"]:
        game["cards"][player.id] = generate_random_card()
        try:
            bot.send_message(player.id, "🎮 **Игра началась!** Вот твоя персональная карточка:")
            send_player_card_private(player.id, game["cards"][player.id])
        except Exception:
            pass

    start_new_round(code)

# --- КАРТОЧКА И СПОСОБНОСТИ В ЛС ---
def send_player_card_private(user_id, card):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Пересдать карту (100 🪙)", callback_data="reroll_private"))
    markup.add(types.InlineKeyboardButton(f"⚡ Активировать: {card['ability']['name']}", callback_data="use_ability_private"))
    
    card_text = (
        "📋 **Твоя карточка выжившего:**\n\n"
        f"👤 Возраст и Пол:\n"
        f"💼 Профессия:\n"
        f"🏥 Здоровье:\n"
        f"🎨 Хобби:\n"
        f"👁 Фобия:\n"
        f"🎒 Инвентарь:\n"
        f"🧬 Фертильность:\n"
        f"📌 Доп. факт:\n\n"
        f"⚡ Фишка:['name']}\n_{card['ability']['desc']}_"
    )
    bot.send_message(user_id, card_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "use_ability_private")
def cb_use_ability(call):
    user_id = call.from_user.id
    code = user_to_game.get(user_id)
    game = active_games.get(code)

    if not game or game.get("status") != "in_progress":
        bot.answer_callback_query(call.id, "Вы сейчас не в активной игре!", show_alert=True)
        return

    if game["used_abilities"].get(user_id, False):
        bot.answer_callback_query(call.id, "Вы уже использовали свою способность в этой игре!", show_alert=True)
        return

    ability = game["cards"][user_id]["ability"]
    game["used_abilities"][user_id] = True

    if ability["id"] == "immunity":
        game["active_immunities"].append(user_id)
        bot.send_message(user_id, "🛡 **Иммунитет активирован!** Вы защищены от вылета в этом раунде.")
        bot.send_message(game["chat_id"], f"🛡 Игрок **{call.from_user.first_name}** активировал **Иммунитет**!")
    elif ability["id"] == "double_vote":
        game["double_votes"].append(user_id)
        bot.send_message(user_id, "✌️ **Двойной голос активирован!** Твой голос посчитается за 2.")
    elif ability["id"] == "reveal_card":
        other_players = [p for p in game["alive"] if p.id != user_id]
        if other_players:
            target = random.choice(other_players)
            target_card = game["cards"][target.id]
            bot.send_message(user_id, f"🔍 **Шпионская сводка по {target.first_name}:**\n💼 Профессия: {target_card['profession']}\n🏥 Здоровье: {target_card['health']}")

    bot.answer_callback_query(call.id, "Способность активирована!")

@bot.callback_query_handler(func=lambda call: call.data == "reroll_private")
def cb_reroll(call):
    user_id = call.from_user.id
    code = user_to_game.get(user_id)
    game = active_games.get(code)
    
    if not game or user_id not in game["cards"]:
        return

    if game["rerolls"].get(user_id, False):
        bot.answer_callback_query(call.id, "Вы уже пересдавали карту!", show_alert=True)
        return

    info = get_user_info(user_id, call.from_user.first_name)
    if not info["vip"]:
        if info["coins"] < 100:
            bot.answer_callback_query(call.id, "Недостаточно монет (нужно 100 🪙)!", show_alert=True)
            return
        update_user_stats(user_id, coins_add=-100)

    game["cards"][user_id] = generate_random_card()
    game["rerolls"][user_id] = True
    bot.answer_callback_query(call.id, "Карта обновлена!")
    send_player_card_private(user_id, game["cards"][user_id])

def start_new_round(code):
    game = active_games.get(code)
    if not game:
        return
        
    event = random.choice(AI_ROUND_EVENTS)
    game["votes"] = {}
    
    msg_text = (
        f"🔄 **РАУНД {game['round']}**\n\n"
        f"⚡ **Происшествие:**\n{event}\n\n"
        f"👥 Выживших: **{len(game['alive'])}** | 🏛 Мест в бункере: **{game['bunker_capacity']}**\n\n"
        f"⏳ **Обсуждайте, кто полезнее! (60 секунд)**"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎴 Моя карта и фишки (в ЛС)", url=f"https://t.me/{BOT_USERNAME}"))

    bot.send_message(game["chat_id"], msg_text, parse_mode="Markdown", reply_markup=markup)
    threading.Thread(target=run_discussion_timer, args=(code, 60)).start()

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
    
    bot.send_message(game["chat_id"], "🗳 **Время вышло! Начинаем голосование!**\n
