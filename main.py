import os
import time
import random
import string
import threading
import telebot
from telebot import types

TOKEN = "8963766433:AAFX8f3AW0IuHq_BDBVPhgU4U3wcMAhjGPA"
bot = telebot.TeleBot(TOKEN)

# Твоя ссылка на официальный канал обновлений
CHANNEL_URL = "https://t.me/bunker_game_official"

# --- БАЗА ДАННЫХ ИГРОКОВ И ИГР ---
user_data = {}      # user_id: {"lang": "ru", "coins": 100, "vip": False}
active_games = {}   # game_code: { "host_id": ..., "players": [...], "status": "lobby", "votes": {}, "cards": {}, "used_abilities": {} }
user_to_game = {}   # user_id: game_code
awaiting_code = {}  # user_id: True

# --- ХАРАКТЕРИСТИКИ ---
PROFESSIONS = ["💼 Врач-хирург", "💼 Инженер-механик", "💼 Агроном", "💼 Строитель", "💼 Ученый-физик", "💼 Повар", "💼 Электрик", "💼 Военный"]
HEALTH_LIST = ["🏥 Абсолютно здоров", "🏥 Легкая аллергия", "🏥 Близорукость (-2)", "🏥 Астма (есть ингалятор)", "🏥 Бессонница"]
HOBBIES = ["🎨 Выживальщик / Туризм", "🎨 Стрельба из лука", "🎨 Боевые искусства", "🎨 Радиолюбитель", "🎨 Огородничество"]
PHOBIAS = ["👁 Боязнь замкнутых пространств", "👁 Темнота", "👁 Высота", "👁 Пауки и насекомые", "👁 Кровь"]
INVENTORIES = ["🎒 Набор инструментов", "🎒 Аптечка первой помощи", "🎒 Зажигалка и фонарик", "🎒 Запас еды на 3 дня", "🎒 Рация"]

ABILITIES = [
    {"id": "double_vote", "name": "✌️ Двойной голос", "desc": "Твой голос при голосовании считается за 2!"},
    {"id": "immunity", "name": "🛡 Иммунитет", "desc": "Защищает тебя от вылета в этом раунде!"},
    {"id": "reveal_card", "name": "🔍 Шпион", "desc": "Позволяет узнать чужую скрытую карту."}
]

EVENTS = [
    "🚨 **Авария в бункере!** Вышла из строя система фильтрации воздуха.",
    "⚠️ **Угроза заражения!** Один из фильтров воды забился.",
    "⚡ **Сбой электросети!** Свет погас на 30 минут..."
]

TEXTS = {
    "ru": {
        "welcome": (
            "👋 **Добро пожаловать в официальную игру «Бункер»!** ☣️\n\n"
            "Выживай, доказывай свою важность и исключай слабых участников!\n\n"
            "📢 **Следи за новостями и обновлениями в нашем канале!**\n"
            "🎮 Создавай комнаты, делись кодом с друзьями и играйте вместе!"
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
        "add_to_chat": "➕ Add to Group 👥",
        "channel_btn": "📢 Updates Channel",
        "create_game": "🎮 Create Game",
        "join_game": "🔗 Join via Code",
        "profile": "👤 Profile & Coins",
        "shop": "💎 VIP Shop (20 ⭐️)",
    }
}

def get_user_info(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"lang": "ru", "coins": 100, "vip": False}
    return user_data[user_id]

def generate_game_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def generate_random_card():
    return {
        "profession": random.choice(PROFESSIONS),
        "health": random.choice(HEALTH_LIST),
        "hobby": random.choice(HOBBIES),
        "phobia": random.choice(PHOBIAS),
        "inventory": random.choice(INVENTORIES),
        "ability": random.choice(ABILITIES)
    }

# --- СТАРТ И ВЫБОР ЯЗЫКА ---
@bot.message_handler(commands=['start'])
def cmd_start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
        types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="set_lang_uz"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")
    )
    bot.send_message(message.chat.id, "🌐 Выберите язык / Tilni tanlang / Choose language:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_lang_"))
def cb_lang(call):
    lang = call.data.split("_")[-1]
    info = get_user_info(call.from_user.id)
    info["lang"] = lang
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
        f"🎮 **Комната создана!**\n\n🔑 Код комнаты: `{code}`\n\nОтправь этот код друзьям, чтобы они подключились!\n\n👥 **Участники в лобби (1):**\n• {user.first_name}",
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
    user_to_game[user.id] = code
    awaiting_code[user.id] = False
    
    bot.send_message(message.chat.id, f"✅ Вы успешно вошли в комнату `{code}`! Ожидаем старта от организатора.", parse_mode="Markdown")
    
    players_list = "\n".join([f"• {p.first_name}" for p in game["players"]])
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Начать игру", callback_data=f"start_game_{code}"))
    
    bot.send_message(
        game["host_id"],
        f"🔔 **Новый игрок зашел!**\n\n🔑 Код: `{code}`\n\n👥 **Участники ({len(game['players'])}):**\n{players_list}",
        parse_mode="Markdown",
        reply_markup=markup
    )

# --- СТАРТ ИГРЫ И КАРТОЧКИ ---
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
    event = random.choice(EVENTS)
    
    bot.send_message(call.message.chat.id, f"🚀 **ИГРА НАЧАЛАСЬ!**\n\n{event}\n\nРассылаем карточки всем игрокам...")
    
    game_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    game_markup.add(types.KeyboardButton("🎴 Моя карта"), types.KeyboardButton("⚡ Использовать способность"))

    for player in game["players"]:
        card = generate_random_card()
        game["cards"][player.id] = card
        
        try:
            bot.send_message(player.id, f"🎮 **Игра началась!**", reply_markup=game_markup)
            send_player_card(player.id, card)
        except Exception:
            pass

    threading.Thread(target=run_discussion_timer, args=(code, 60)).start()

def send_player_card(user_id, card):
    card_text = (
        "📋 **Твоя карточка выжившего:**\n\n"
        + card['profession'] + "\n"
        + card['health'] + "\n"
        + card['hobby'] + "\n"
        + card['phobia'] + "\n"
        + card['inventory'] + "\n\n"
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
    
    if game and user_id in game["cards"]:
        if user_id in game["used_abilities"]:
            bot.reply_to(message, "⚠️ Вы уже использовали свою способность!")
            return
        ability = game["cards"][user_id]["ability"]
        game["used_abilities"][user_id] = ability["id"]
        
        for p in game["players"]:
            bot.send_message(p.id, f"💥 **{message.from_user.first_name}** активировал фишку: **{ability['name']}**!")

# --- ТАЙМЕР И ГОЛОСОВАНИЕ ---
def run_discussion_timer(code, seconds):
    time.sleep(seconds)
    if code in active_games:
        start_voting_phase(code)

def start_voting_phase(code):
    game = active_games.get(code)
    if not game:
        return
        
    markup = types.InlineKeyboardMarkup()
    for player in game["players"]:
        markup.add(types.InlineKeyboardButton(f"❌ Исключить {player.first_name}", callback_data=f"vote_{code}_{player.id}"))
    
    for player in game["players"]:
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
    
    if len(game["votes"]) >= len(game["players"]):
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
    
    for p in game["players"]:
        info = get_user_info(p.id)
        info["coins"] += 20
        
        if kicked_id and game["used_abilities"].get(kicked_id) == "immunity":
            bot.send_message(p.id, "🛡 **Игрок защитился иммунитетом!** Никто не вылетает.")
        elif kicked_id:
            kicked_player = next((pl for pl in game["players"] if pl.id == kicked_id), None)
            if kicked_player:
                bot.send_message(p.id, f"❌ **Игрок {kicked_player.first_name} исключен из бункера!**\n🪙 Всем участникам начислено +20 монет!")

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
    info["vip"] = True
    info["coins"] += 500
    bot.send_message(message.chat.id, "🎉 **Поздравляем! Вы успешно купили VIP за 20 Stars!** 👑\nВам также начислено 500 монет!")

if __name__ == "__main__":
    print("Бот обновлен и запущен!")
    bot.infinity_polling()
