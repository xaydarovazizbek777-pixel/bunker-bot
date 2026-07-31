import os
import time
import random
import threading
import telebot
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
bot = telebot.TeleBot(TOKEN)

user_data = {}      # user_id: {"lang": "ru"}
active_games = {}   # chat_id: { "players": [...], "votes": {}, "cards": {}, "used_abilities": {} }

# --- БАЗА ДАННЫХ ХАРАКТЕРИСТИК И СПОСОБНОСТЕЙ ---
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
    "🚨 **Авария в бункере!** Вышла из строя система фильтрации воздуха. Нужно срочно решить, кто полезет чинить!",
    "⚠️ **Угроза заражения!** Один из фильтров воды забился. Ресурсов осталось меньше!",
    "⚡ **Сбой электросети!** Свет погас на 30 минут, атмосфера накаляется..."
]

TEXTS = {
    "ru": {
        "welcome": "👋 **Добро пожаловать в игру «Бункер»!** ☣️\n\nВыберите действие или добавьте бота в чат:",
        "add_to_chat": "➕ Добавить бота в чат 👥",
        "create_game": "🎮 Создать игру",
        "join_game": "🔗 Подключиться",
        "profile": "👤 Профиль",
        "shop": "💎 VIP / Магазин",
        "discussion_start": "⏱ **Бот запустил таймер обсуждения (60 сек)!** ⏳\nИзучите свои карты и докажите, почему вы должны выжить!",
        "voting_start": "🗳 **Время на обсуждение вышло! Начинаем голосование!** ❌\nВыберите игрока, которого нужно исключить:",
        "player_kicked": "❌ **Игрок {name} исключен из бункера!**\n\n🔓 **Его раскрытые характеристики:**\n• {prof}\n• {health}\n• {hobby}\n• {phobia}\n• {inv}\n• ⚡ **Фишка:** {ability}",
        "nobody_kicked": "🤝 Голоса разделились или сработал иммунитет! Никто не вылетел."
    },
    "uz": {
        "welcome": "👋 **«Bunker» o'yiniga xush kelibsiz!** ☣️\n\nTugmani tanlang yoki botni guruhga qo'shing:",
        "add_to_chat": "➕ Botni guruhga qo'shish 👥",
        "create_game": "🎮 O'yin yaratish",
        "join_game": "🔗 Qo'shilish",
        "profile": "👤 Profil",
        "shop": "💎 VIP / Do'kon",
        "discussion_start": "⏱ **Muhokama taymeri boshlandi (60 soniya)!** ⏳\nO'z kartalaringizni ko'ring va tirik qolishga loyiq ekanligingizni isbotlang!",
        "voting_start": "🗳 **Ovoz berish vaqti boshlandi!** ❌\nBunkerdan kimni chiqarib yuborishni tanlang:",
        "player_kicked": "❌ **O'yinchi {name} bunkerdan chiqarildi!**\n\n🔓 **Uning barcha kartalari ochildi:**\n• {prof}\n• {health}\n• {hobby}\n• {phobia}\n• {inv}\n• ⚡ **Qobiliyati:** {ability}",
        "nobody_kicked": "🤝 Ovozlar teng bo'ldi! Hech kim chiqib ketmadi."
    },
    "en": {
        "welcome": "👋 **Welcome to «Bunker» game!** ☣️\n\nChoose an action or add the bot to your group:",
        "add_to_chat": "➕ Add Bot to Group 👥",
        "create_game": "🎮 Create Game",
        "join_game": "🔗 Join Game",
        "profile": "👤 Profile",
        "shop": "💎 VIP / Shop",
        "discussion_start": "⏱ **Discussion timer started (60s)!** ⏳\nCheck your cards and prove why you should survive!",
        "voting_start": "🗳 **Voting time started!** ❌\nVote to kick a player from the bunker:",
        "player_kicked": "❌ **Player {name} was kicked from the bunker!**\n\n🔓 **Revealed cards:**\n• {prof}\n• {health}\n• {hobby}\n• {phobia}\n• {inv}\n• ⚡ **Ability:** {ability}",
        "nobody_kicked": "🤝 Votes were tied or immunity was used! No one was kicked."
    }
}

def get_lang(user_id):
    return user_data.get(user_id, {}).get("lang", "ru")

def generate_random_card():
    return {
        "profession": random.choice(PROFESSIONS),
        "health": random.choice(HEALTH_LIST),
        "hobby": random.choice(HOBBIES),
        "phobia": random.choice(PHOBIAS),
        "inventory": random.choice(INVENTORIES),
        "ability": random.choice(ABILITIES)
    }

# --- КОМАНДЫ СТАРТА И ЯЗЫКОВ ---
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
    user_data[call.from_user.id] = {"lang": lang}
    bot.answer_callback_query(call.id, "OK! 👌")
    show_main_menu(call.message.chat.id, call.from_user.id)

def show_main_menu(chat_id, user_id):
    lang = get_lang(user_id)
    bot_username = bot.get_me().username
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton(TEXTS[lang]["create_game"]),
        types.KeyboardButton(TEXTS[lang]["join_game"])
    )
    markup.add(
        types.KeyboardButton(TEXTS[lang]["profile"]),
        types.KeyboardButton(TEXTS[lang]["shop"])
    )
    
    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(types.InlineKeyboardButton(TEXTS[lang]["add_to_chat"], url=f"https://t.me/{bot_username}?startgroup=true"))

    bot.send_message(chat_id, TEXTS[lang]["welcome"], reply_markup=markup, parse_mode="Markdown")
    bot.send_message(chat_id, "📢 Добавить бота в группу:", reply_markup=inline_markup)

# --- СОЗДАНИЕ ИГРЫ И ВЫДАЧА КАРТ ---
@bot.message_handler(commands=['create', 'start_game'])
@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["create_game"], TEXTS["uz"]["create_game"], TEXTS["en"]["create_game"]])
def cmd_create_game(message):
    chat_id = message.chat.id
    user = message.from_user
    lang = get_lang(user.id)
    
    user_card = generate_random_card()
    event = random.choice(EVENTS)
    
    active_games[chat_id] = {
        "players": [user],
        "votes": {},
        "cards": {user.id: user_card},
        "used_abilities": {}
    }
    
    game_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    game_markup.add(types.KeyboardButton("🎴 Моя карта"), types.KeyboardButton("⚡ Использовать способность"))
    
    bot.send_message(chat_id, f"🎮 **Игра «Бункер» начата!**\n\n{event}\n\n{TEXTS[lang]['discussion_start']}", reply_markup=game_markup, parse_mode="Markdown")
    
    send_player_card(chat_id, user.id, user_card)
    threading.Thread(target=run_discussion_timer, args=(chat_id, 60)).start()

def send_player_card(chat_id, user_id, card):
    card_text = (
        f"📋 **Твоя карточка выжившего:**\n\n"
        f"{card['profession']}\n"
        f"{card['health']}\n"
        f"{card['hobby']}\n"
        f"{card['phobia']}\n"
        f"{card['inventory']}\n\n"
        f"⚡ Особая фишка:['name']}\n"
        f"📝 _{card['ability']['desc']}_"
    )
    bot.send_message(chat_id, card_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🎴 Моя карта")
def show_my_card(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    game = active_games.get(chat_id)
    if game and user_id in game["cards"]:
        send_player_card(chat_id, user_id, game["cards"][user_id])

@bot.message_handler(func=lambda m: m.text == "⚡ Использовать способность")
def use_ability(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    game = active_games.get(chat_id)
    
    if game and user_id in game["cards"]:
        if user_id in game["used_abilities"]:
            bot.reply_to(message, "⚠️ Вы уже использовали свою способность!")
            return
        
        ability = game["cards"][user_id]["ability"]
        game["used_abilities"][user_id] = ability["id"]
        bot.send_message(chat_id, f"💥 **{message.from_user.first_name}** активировал фишку: **{ability['name']}**!")

# --- АВТО-ТАЙМЕР И ГОЛОСОВАНИЕ ---
def run_discussion_timer(chat_id, seconds):
    time.sleep(seconds)
    if chat_id in active_games:
        start_voting_phase(chat_id)

def start_voting_phase(chat_id):
    game = active_games.get(chat_id)
    if not game:
        return
    
    markup = types.InlineKeyboardMarkup()
    for player in game["players"]:
        markup.add(types.InlineKeyboardButton(f"❌ Исключить {player.first_name}", callback_data=f"vote_{player.id}"))
    
    bot.send_message(chat_id, "🗳 **Время на обсуждение вышло! Начинаем голосование!** 🔥\nВыберите игрока для исключения:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vote_"))
def cb_vote(call):
    chat_id = call.message.chat.id
    voter_id = call.from_user.id
    target_id = int(call.data.split("_")[1])
    
    game = active_games.get(chat_id)
    if not game:
        bot.answer_callback_query(call.id, "Игра не найдена.")
        return
    
    game["votes"][voter_id] = target_id
    bot.answer_callback_query(call.id, "Ваш голос принят! 🗳")
    
    if len(game["votes"]) >= len(game["players"]):
        finish_voting(chat_id)

def finish_voting(chat_id):
    game = active_games.get(chat_id)
    if not game:
        return
    
    vote_counts = {}
    for voter, target in game["votes"].items():
        weight = 2 if game["used_abilities"].get(voter) == "double_vote" else 1
        vote_counts[target] = vote_counts.get(target, 0) + weight
    
    if not vote_counts:
        bot.send_message(chat_id, TEXTS["ru"]["nobody_kicked"])
        return

    kicked_id = max(vote_counts, key=vote_counts.get)
    
    if game["used_abilities"].get(kicked_id) == "immunity":
        bot.send_message(chat_id, "🛡 **Игрок защитился иммунитетом!** Никто не вылетает в этом раунде!")
        game["votes"] = {}
        return

    kicked_player = next((p for p in game["players"] if p.id == kicked_id), None)
    
    if kicked_player:
        cards = game["cards"].get(kicked_id, generate_random_card())
        msg = TEXTS["ru"]["player_kicked"].format(
            name=kicked_player.first_name,
            prof=cards["profession"],
            health=cards["health"],
            hobby=cards["hobby"],
            phobia=cards["phobia"],
            inv=cards["inventory"],
            ability=cards["ability"]["name"]
        )
        bot.send_message(chat_id, msg, parse_mode="Markdown")
        
        game["players"] = [p for p in game["players"] if p.id != kicked_id]
        game["votes"] = {}

# --- ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ ---
@bot.message_handler(commands=['profile'])
@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["profile"], TEXTS["uz"]["profile"], TEXTS["en"]["profile"]])
def cmd_profile(message):
    bot.send_message(message.chat.id, f"👤 **Профиль**\n\nID: `{message.from_user.id}`\nСыграно игр: 0\nПобед: 0 🏆", parse_mode="Markdown")

@bot.message_handler(commands=['shop'])
@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["shop"], TEXTS["uz"]["shop"], TEXTS["en"]["shop"]])
def cmd_shop(message):
    bot.send_message(message.chat.id, "💎 **VIP Магазин**\n\nПокупка уникальных скинов карт и VIP статусов! ✨")

if __name__ == "__main__":
    print("Бот обновлен и запущен!")
    bot.infinity_polling()
