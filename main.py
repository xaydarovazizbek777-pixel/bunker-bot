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
CHANNEL_URL = "https://t.me/bunker_game_official"

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
        types.BotCommand("shop", "🛍 Магазин и VIP"),
        types.BotCommand("top", "🏆 Таблица лидеров (Топ-10)"),
        types.BotCommand("lang", "🌐 Сменить язык / Language"),
        types.BotCommand("rules", "📖 Правила игры")
    ]
    try:
        bot.set_my_commands(commands)
        print("✅ Меню команд (/) успешно установлено!")
    except Exception as e:
        print("⚠️ Ошибка установки меню команд: " + str(e))

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
            title TEXT DEFAULT 'Выживший',
            medkit INTEGER DEFAULT 0,
            radio INTEGER DEFAULT 0,
            knife INTEGER DEFAULT 0,
            armor INTEGER DEFAULT 0,
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
    cursor.execute("SELECT lang, coins, vip, title, medkit, radio, knife, armor, rating, games_played, games_won, last_bonus FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute(
            "INSERT INTO users (user_id, username, lang, coins, vip, title, rating, games_played, games_won) VALUES (?, ?, 'ru', 100, 0, 'Выживший', 1000, 0, 0)",
            (user_id, username)
        )
        conn.commit()
        info = {
            "lang": "ru", "coins": 100, "vip": False, "title": "Выживший",
            "medkit": 0, "radio": 0, "knife": 0, "armor": 0,
            "rating": 1000, "played": 0, "won": 0, "last_bonus": None
        }
    else:
        cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        conn.commit()
        info = {
            "lang": row[0], "coins": row[1], "vip": bool(row[2]), "title": row[3],
            "medkit": row[4], "radio": row[5], "knife": row[6], "armor": row[7],
            "rating": row[8], "played": row[9], "won": row[10], "last_bonus": row[11]
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

# --- ЯЗЫКОВЫЕ ТЕКСТЫ ---
TEXTS = {
    "ru": {
        "welcome": "👋 **Добро пожаловать в «Бункер»!** ☣️\n\nИспользуй меню ниже для управления профилем и игрой!",
        "create_game": "🎮 Создать игру",
        "join_game": "🔗 Подключиться по коду",
        "profile": "👤 Профиль",
        "shop": "🛍 Магазин",
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
        "shop": "🛍 Do'kon",
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
        "shop": "🛍 Shop",
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

ROUND_CATEGORIES = {
    1: ("prof_age", "💼 Профессия + 👤 Пол и Возраст"),
    2: ("health_inv", "🏥 Здоровье + 🎒 Инвентарь"),
    3: ("hobby_phobia", "🎨 Хобби + 👁 Фобия"),
    4: ("fert_fact", "🧬 Фертильность + 📌 Доп. факт")
}

active_games = {}   
user_to_game = {}   

def generate_game_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def generate_random_card():
    gender = random.choice(["👨 Мужчина", "👩 Женщина"])
    age = random.randint(18, 65)
    return {
        "gender_age": gender + ", " + str(age) + " лет",
        "profession": random.choice(PROFESSIONS),
        "health": random.choice(HEALTH_LIST),
        "hobby": random.choice(HOBBIES),
        "phobia": random.choice(PHOBIAS),
        "inventory": random.choice(INVENTORIES),
        "fertility": random.choice(FERTILITY),
        "fact": random.choice(FACTS),
        "ability": random.choice(ABILITIES)
    }

# --- ОБРАБОТКА /START И ССЫЛОК ---
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

    # Кнопки основного меню
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    reply_markup.add(types.KeyboardButton(t["create_game"]), types.KeyboardButton(t["join_game"]))
    reply_markup.add(types.KeyboardButton(t["profile"]), types.KeyboardButton(t["top"]))
    reply_markup.add(types.KeyboardButton(t["daily"]), types.KeyboardButton(t["shop"]))
    reply_markup.add(types.KeyboardButton(t["ref"]), types.KeyboardButton(t["lang"]))
    
    # Инлайн-ссылки под сообщением
    inline_markup = types.InlineKeyboardMarkup()
    add_group_url = "https://t.me/" + BOT_USERNAME + "?startgroup=true"
    inline_markup.add(types.InlineKeyboardButton("➕ Добавить бота в группу", url=add_group_url))
    inline_markup.add(types.InlineKeyboardButton("📢 Канал обновлений", url=CHANNEL_URL))

    bot.send_message(chat_id, t["welcome"], reply_markup=reply_markup, parse_mode="Markdown")
    bot.send_message(chat_id, "📌 **Быстрые ссылки:**", reply_markup=inline_markup, parse_mode="Markdown")

@bot.message_handler(commands=['lang'])
@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["lang"], TEXTS["uz"]["lang"], TEXTS["en"]["lang"]])
def cmd_change_lang(message):
    if message.chat.type != 'private':
        return

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
        "📖 **Правила игры «Бункер»:**\n\n1️⃣ На Земле произошла катастрофа.\n2️⃣ У каждого игрока есть уникальная карта характеристик в ЛС.\n3️⃣ Каждый раунд игроки открывают по 2 характеристики и доказывают свою полезность.\n4️⃣ Голосованием выбывают самые непригодные!",
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
    
    text = (
        "👤 **Профиль выжившего:**\n\n"
        "🆔 ID: `" + str(message.from_user.id) + "`\n"
        "🏷 Титул: **" + str(info['title']) + "**\n"
        "✨ Статус: " + vip_status + "\n"
        "🪙 Монеты: **" + str(info['coins']) + "**\n"
        "🏆 Рейтинг: **" + str(info['rating']) + " РТС**\n\n"
        "🎒 **Инвентарь предметов:**\n"
        "• 🩹 Аптечка: " + str(info['medkit']) + " шт.\n"
        "• 📻 Рация: " + str(info['radio']) + " шт.\n"
        "• 🔪 Охотничий нож: " + str(info['knife']) + " шт.\n"
        "• 🛡 Бронежилет: " + str(info['armor']) + " шт.\n\n"
        "📊 Игр: **" + str(info['played']) + "** | Побед: **" + str(info['won']) + "** (" + str(winrate) + "%)"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

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
        text += str(idx+1) + ". **" + str(user[0]) + "** — " + str(user[1]) + " РТС | 🏆 " + str(user[2]) + " побед\n"

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

# --- МАГАЗИН И ПОКУПКА VIP ЗА 10 STARS ---
@bot.message_handler(commands=['shop'])
@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["shop"], TEXTS["uz"]["shop"], TEXTS["en"]["shop"]])
def handle_shop(message):
    if message.chat.type != 'private':
        return

    info = get_user_info(message.from_user.id, message.from_user.first_name)
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    markup.add(
        types.InlineKeyboardButton("⭐ VIP-Статус — 10 Stars", callback_data="buy_vip_10stars"),
        types.InlineKeyboardButton("🩹 Аптечка (150 🪙)", callback_data="buy_item_medkit"),
        types.InlineKeyboardButton("📻 Рация (120 🪙)", callback_data="buy_item_radio"),
        types.InlineKeyboardButton("🔪 Охотничий нож (100 🪙)", callback_data="buy_item_knife"),
        types.InlineKeyboardButton("🛡 Бронежилет (200 🪙)", callback_data="buy_item_armor"),
        types.InlineKeyboardButton("🏷 Титул «Легенда Бункера» (300 🪙)", callback_data="buy_title_legend"),
        types.InlineKeyboardButton("👑 Титул «Хозяин Пустоши» (500 🪙)", callback_data="buy_title_wasteland")
    )

    shop_text = (
        "🛍 **МАГАЗИН «БУНКЕР»**\n\n"
        "🪙 Твой баланс: **" + str(info['coins']) + " монет**\n\n"
        "👑 **VIP-Статус (10 ⭐ Stars):**\n"
        "• Бесплатная пересдача карт во всех играх!\n"
        "• +500 монет мгновенно при покупке!\n"
        "• Особый значок VIP возле ника.\n\n"
        "🛒 Выберите товар для покупки ниже:"
    )
    bot.send_message(message.chat.id, shop_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "buy_vip_10stars")
def cb_buy_vip_stars(call):
    prices = [types.LabeledPrice(label="VIP Статус в Бункере", amount=10)]
    bot.send_invoice(
        call.message.chat.id,
        title="👑 VIP-Статус «Бункер»",
        description="Эксклюзивный статус VIP, +500 монет и бесплатные пересдачи карт!",
        invoice_payload="vip_subscription_10_stars",
        provider_token="", # Для Stars токен пустой
        currency="XTR",
        prices=prices
    )

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message):
    user_id = message.from_user.id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET vip = 1, coins = coins + 500 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    bot.send_message(message.chat.id, "🎉 **Поздравляем с покупкой VIP!**\n👑 Вам присвоен VIP-Статус и зачислено **+500 монет** 🪙!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def cb_buy_shop_items(call):
    user_id = call.from_user.id
    item = call.data.replace("buy_", "")
    info = get_user_info(user_id, call.from_user.first_name)
    
    conn = get_db()
    cursor = conn.cursor()
    
    if item == "item_medkit":
        if info["coins"] < 150:
            bot.answer_callback_query(call.id, "❌ Недостаточно монет (нужно 150 🪙)!", show_alert=True)
            return
        cursor.execute("UPDATE users SET coins = coins - 150, medkit = medkit + 1 WHERE user_id = ?", (user_id,))
        bot.answer_callback_query(call.id, "✅ Вы купили Аптечку 🩹!")
        
    elif item == "item_radio":
        if info["coins"] < 120:
            bot.answer_callback_query(call.id, "❌ Недостаточно монет (нужно 120 🪙)!", show_alert=True)
            return
        cursor.execute("UPDATE users SET coins = coins - 120, radio = radio + 1 WHERE user_id = ?", (user_id,))
        bot.answer_callback_query(call.id, "✅ Вы купили Рацию 📻!")
        
    elif item == "item_knife":
        if info["coins"] < 100:
            bot.answer_callback_query(call.id, "❌ Недостаточно монет (нужно 100 🪙)!", show_alert=True)
            return
        cursor.execute("UPDATE users SET coins = coins - 100, knife = knife + 1 WHERE user_id = ?", (user_id,))
        bot.answer_callback_query(call.id, "✅ Вы купили Охотничий нож 🔪!")
        
    elif item == "item_armor":
        if info["coins"] < 200:
            bot.answer_callback_query(call.id, "❌ Недостаточно монет (нужно 200 🪙)!", show_alert=True)
            return
        cursor.execute("UPDATE users SET coins = coins - 200, armor = armor + 1 WHERE user_id = ?", (user_id,))
        bot.answer_callback_query(call.id, "✅ Вы купили Бронежилет 🛡!")
        
    elif item == "title_legend":
        if info["coins"] < 300:
            bot.answer_callback_query(call.id, "❌ Недостаточно монет (нужно 300 🪙)!", show_alert=True)
            return
        cursor.execute("UPDATE users SET coins = coins - 300, title = '☣️ Легенда Бункера' WHERE user_id = ?", (user_id,))
        bot.answer_callback_query(call.id, "✅ Куплен титул «Легенда Бункера»!")

    elif item == "title_wasteland":
        if info["coins"] < 500:
            bot.answer_callback_query(call.id, "❌ Недостаточно монет (нужно 500 🪙)!", show_alert=True)
            return
        cursor.execute("UPDATE users SET coins = coins - 500, title = '👑 Хозяин Пустоши' WHERE user_id = ?", (user_id,))
        bot.answer_callback_query(call.id, "✅ Куплен титул «Хозяин Пустоши»!")

    conn.commit()
    conn.close()

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
        "revealed_traits": {}, 
        "used_abilities": {},
        "active_immunities": [],
        "double_votes": [],
        "rerolls": {}
    }
    user_to_game[user.id] = code
    
    join_link = "https://t.me/" + BOT_USERNAME + "?start=join_" + code
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Войти в игру", url=join_link))
    markup.add(types.InlineKeyboardButton("🚀 Начать игру", callback_data="start_game_" + code))

    msg = (
        "🎮 **ИГРА СОЗДАНА!**\n\n"
        "🔑 Код комнаты: `" + code + "`\n\n"
        "🌍 **Катастрофа:**\n" + catastrophe + "\n\n"
        "👥 **В лобби:** " + user.first_name + "\n\n"
        "Нажмите кнопку ниже, чтобы войти!"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

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
    
    bot.send_message(message.chat.id, "✅ Вы вошли в игру `" + code + "`! Ожидайте старта.", parse_mode="Markdown")
    
    players_list = ", ".join([p.first_name for p in game["players"]])
    bot.send_message(game["chat_id"], "🔔 **" + user.first_name + "** вошел в игру!\n👥 **Участники (" + str(len(game['players'])) + "):** " + players_list)

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
        game["revealed_traits"][player.id] = []
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
    markup.add(types.InlineKeyboardButton("⚡ Активировать: " + card['ability']['name'], callback_data="use_ability_private"))
    
    card_text = (
        "📋 **Твоя карточка выжившего:**\n\n"
        "👤 **Возраст и Пол:** " + card['gender_age'] + "\n"
        "💼 **Профессия:** " + card['profession'] + "\n"
        "🏥 **Здоровье:** " + card['health'] + "\n"
        "🎨 **Хобби:** " + card['hobby'] + "\n"
        "👁 **Фобия:** " + card['phobia'] + "\n"
        "🎒 **Инвентарь:** " + card['inventory'] + "\n"
        "🧬 **Фертильность:** " + card['fertility'] + "\n"
        "📌 **Доп. факт:** " + card['fact'] + "\n\n"
        "⚡ **Фишка:** " + card['ability']['name'] + "\n"
        "_" + card['ability']['desc'] + "_"
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
        bot.send_message(game["chat_id"], "🛡 Игрок **" + call.from_user.first_name + "** активировал **Иммунитет**!")
    elif ability["id"] == "double_vote":
        game["double_votes"].append(user_id)
        bot.send_message(user_id, "✌️ **Двойной голос активирован!** Твой голос посчитается за 2.")
    elif ability["id"] == "reveal_card":
        other_players = [p for p in game["alive"] if p.id != user_id]
        if other_players:
            target = random.choice(other_players)
            target_card = game["cards"][target.id]
            bot.send_message(user_id, "🔍 **Шпионская сводка по " + target.first_name + ":**\n💼 Профессия: " + target_card['profession'] + "\n🏥 Здоровье: " + target_card['health'])

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
    
    round_num = min(game["round"], 4)
    trait_key, trait_name = ROUND_CATEGORIES[round_num]

    msg_text = (
        "🔄 **РАУНД " + str(game['round']) + "**\n\n"
        "⚡ **Происшествие:**\n" + event + "\n\n"
        "📢 **Тема раунда:** Открываем **" + trait_name + "**!\n"
        "✉️ *Всем выжившим отправлена кнопка для раскрытия 2-х характеристик в ЛС бота!*\n\n"
        "👥 Выживших: **" + str(len(game['alive'])) + "** | 🏛 Мест в бункере: **" + str(game['bunker_capacity']) + "**\n\n"
        "⏳ **Обсуждайте 50 секунд!**"
    )
    
    bot.send_message(game["chat_id"], msg_text, parse_mode="Markdown")

    for player in game["alive"]:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔓 Открыть 2 характеристики в чат", callback_data="reveal_trait_" + code))
        try:
            bot.send_message(player.id, "📢 **Раунд " + str(game['round']) + ":** Нажми кнопку, чтобы открыто показать **" + trait_name + "** в общий чат!", reply_markup=markup)
        except Exception:
            pass

    threading.Thread(target=run_discussion_timer, args=(code, 50)).start()

@bot.callback_query_handler(func=lambda call: call.data.startswith("reveal_trait_"))
def cb_reveal_trait(call):
    code = call.data.split("_")[-1]
    game = active_games.get(code)
    user_id = call.from_user.id

    if not game or user_id not in [p.id for p in game["alive"]]:
        bot.answer_callback_query(call.id, "Вы не выживший в этой игре!", show_alert=True)
        return

    round_num = min(game["round"], 4)
    trait_key, trait_name = ROUND_CATEGORIES[round_num]

    if trait_key in game["revealed_traits"].get(user_id, []):
        bot.answer_callback_query(call.id, "Вы уже открыли эти характеристики в этом раунде!", show_alert=True)
        return

    card = game["cards"][user_id]
    game["revealed_traits"][user_id].append(trait_key)

    trait_value = ""
    if trait_key == "prof_age":
        trait_value = "💼 **Профессия:** " + card["profession"] + "\n👤 **Пол и Возраст:** " + card["gender_age"]
    elif trait_key == "health_inv":
        trait_value = "🏥 **Здоровье:** " + card["health"] + "\n🎒 **Инвентарь:** " + card["inventory"]
    elif trait_key == "hobby_phobia":
        trait_value = "🎨 **Хобби:** " + card["hobby"] + "\n👁 **Фобия:** " + card["phobia"]
    elif trait_key == "fert_fact":
        trait_value = "🧬 **Фертильность:** " + card["fertility"] + "\n📌 **Доп. факт:** " + card["fact"]

    bot.answer_callback_query(call.id, "Характеристики отправлены в чат!")
    
    bot.send_message(
        game["chat_id"],
        "📢 **" + call.from_user.first_name + "** раскрыл свои данные:\n\n" + trait_value,
        parse_mode="Markdown"
    )

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
        markup.add(types.InlineKeyboardButton("❌ Исключить " + player.first_name, callback_data="vote_" + code + "_" + str(player.id)))
    
    bot.send_message(game["chat_id"], "🗳 **Время для обсуждения вышло! Начинаем голосование!**\nВыберите, кого выгнать из бункера:", reply_markup=markup)
    threading.Thread(target=run_voting_timer, args=(code, 45)).start()

def run_voting_timer(code, seconds):
    time.sleep(seconds)
    game = active_games.get(code)
    if game and game.get("status") == "in_progress":
        finish_voting(code)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vote_"))
def cb_vote(call):
    parts = call.data.split("_")
    code, target_id, voter_id = parts[1], int(parts[2]), call.from_user.id
    game = active_games.get(code)
    
    if not game or voter_id not in [p.id for p in game["alive"]]:
        bot.answer_callback_query(call.id, "Вы не можете голосовать!")
        return
        
    vote_weight = 2 if voter_id in game["double_votes"] else 1
    game["votes"][voter_id] = (target_id, vote_weight)
    bot.answer_callback_query(call.id, "Голос принят! 🗳")
    
    if len(game["votes"]) >= len(game["alive"]):
        finish_voting(code)

def finish_voting(code):
    game = active_games.get(code)
    if not game or "finished_vote" in game:
        return
        
    game["finished_vote"] = True
    vote_counts = {}
    for voter, (target, weight) in game["votes"].items():
        vote_counts[target] = vote_counts.get(target, 0) + weight
        
    kicked_id = max(vote_counts, key=vote_counts.get) if vote_counts else None
    
    if kicked_id in game["active_immunities"]:
        bot.send_message(game["chat_id"], "🛡 Игрок защищен **Иммунитетом**! Никто не вылетает в этом раунде.")
        game["active_immunities"].remove(kicked_id)
    elif kicked_id:
        kicked_player = next((pl for pl in game["alive"] if pl.id == kicked_id), None)
        if kicked_player:
            game["alive"].remove(kicked_player)
            update_user_stats(kicked_id, rating_add=-10)
            bot.send_message(game["chat_id"], "❌ **Результаты голосования:** Игрок **" + kicked_player.first_name + "** исключен из бункера!")

    del game["finished_vote"]

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

    winners_list = "\n".join(["🏆 " + p.first_name for p in game["alive"]])
    
    for p in game["players"]:
        if p in game["alive"]:
            update_user_stats(p.id, coins_add=100, rating_add=25, win=True)
            
    bot.send_message(
        game["chat_id"],
        "🎉 **ИГРА ЗАВЕРШЕНА!** ☣️\n\nПобедители, попавшие в бункер:\n" + winners_list + "\n\n🏆 Победители получают **+100 монет** и **+25 РТС**!",
        parse_mode="Markdown"
    )
    del active_games[code]

# --- РЕФЕРАЛЬНАЯ СИСТЕМА ---
@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["ref"], TEXTS["uz"]["ref"], TEXTS["en"]["ref"]])
def handle_ref(message):
    if message.chat.type != 'private':
        return
    ref_link = "https://t.me/" + BOT_USERNAME + "?start=ref_" + str(message.from_user.id)
    bot.send_message(message.chat.id, "🤝 **Реферальная программа**\n\nПриглашай друзей и получай **100 монет** 🪙!\n\n🔗 Твоя ссылка:\n`" + ref_link + "`", parse_mode="Markdown")

if __name__ == "__main__":
    setup_bot_commands()
    threading.Thread(target=run_flask, daemon=True).start()
    print("Бот запущен и готов к работе!")
    bot.infinity_polling()
