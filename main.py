import os
import random
import threading
from flask import Flask
import telebot
from telebot import types

# --- 1. Flask-сервер для Render (24/7) ---
app = Flask('')

@app.route('/')
def home():
    return "Bunker Ultimate Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask).start()

# --- 2. Инициализация Бота ---
TOKEN = os.environ.get("BOT_TOKEN", "8963766433:AAFX8f3AW0IuHq_BDBVPhgU4U3wcMAhjGPA")
bot = telebot.TeleBot(TOKEN)

# Хранилища данных
private_rooms = {} 
user_states = {}   
players = {}       
user_languages = {} 
votes = {}         
user_balances = {}  
user_titles = {}    
vip_users = set()   

# --- 3. Катастрофы и ЧП ---
DISASTERS_RU = [
    "☄️ **Падение метеорита:** Атмосфера заполнена пылью, наступила вечная ночь. Температура -40°C.",
    "☣️ **Ядерная зима:** Радиационный фон превышен в 100 раз. На поверхности жить невозможно.",
    "🧟‍♂️ **Зомби-вирус:** 99% населения превратились в мутантов. Бункер — последнее укрытие.",
    "🤖 **Восстание ИИ:** Роботы захватили поверхность и уничтожают всё живое."
]

DISASTERS_UZ = [
    "☄️ **Meteorit tushishi:** Atmosfera chang bilan to'lgan, abadiy tun tushdi. Harorat -40°C.",
    "☣️ **Yadroviy qish:** Radiatsiya darajasi 100 baravar oshdi. Yer yuzida yashash imkonsiz.",
    "🧟‍♂️ **Zombi-virus:** Aholining 99 foizi mutantlarga aylandi. Bunker — yagona boshpana.",
    "🤖 **AI isyoni:** Robotlar yer yuzini egalladi va barcha tirik mavjudotlarni yo'q qilmoqda."
]

EVENTS_RU = [
    "⚡ **ЧП: Замыкание проводки!** Напряжение растёт, все спорят в два раза громче!",
    "🥫 **ЧП: Утік кислорода!** Дышать становится труднее, времени на раздумья меньше.",
    "🎁 **ЧП: Тайный схрон!** В вентиляции нашли старые запасы (+50 монет всем живым в конце раунда)!",
    "🛡️ **ЧП: Сбой системы!** В этом раунде изгнание отменяется, все остаются в бункере!"
]

# --- 4. Тексты ---
TEXTS = {
    'ru': {
        'welcome': "👋 Привет, **{name}**!\n\nВыбери язык / Tilni tanlang:",
        'start_menu': "☣️ **БУНКЕР ULTIMATE EDITION** ☣️\n\nИграй, покупай VIP за звёзды, участвуй в ЧП и побеждай!",
        'btn_create': "➕ Создать комнату",
        'btn_join': "🚪 Войти по коду",
        'btn_card': "📜 Моя карта",
        'btn_reveal': "👁 Открыть черту",
        'btn_profile': "👤 Профиль / VIP 🌟",
        'btn_shop': "🛒 Магазин титулов",
        'btn_vip': "⭐ Купить VIP (20 Звёзд)",
        'btn_players': "👥 Игроки",
        'btn_vote': "🗳 Голосование + ЧП",
        'btn_start_game': "🚀 Начать игру (Хост)",
        'btn_disaster': "🌪 Катастрофа",
        'btn_bunker': "🏛 Бункер",
        'btn_rules': "📖 Правила",
        'btn_lang': "🌐 Язык",
        'room_created': "🚨 **ИГРА СОЗДАНА!** 🚨\n🔑 Код комнаты: `{code}`",
        'enter_code': "🔢 Введи 4-значный код комнаты:",
        'room_not_found': "❌ Комната не найдена.",
        'room_joined': "✅ Ты вошел в комнату `#{code}`!",
        'game_started_msg': "🚀 **ИГРА НАЧАЛАСЬ!**",
        'card_title': "📜 **ТВОЯ КАРТА ВЫЖИВШЕГО** 🧟‍♂️",
        'prof': "💼 Профессия",
        'health': "🩺 Здоровье",
        'bio': "🧬 Биология",
        'hobby': "⚽ Хобби",
        'inventory': "🎒 Багаж",
        'phobia': "🎭 Характер / Фобия",
        'special': "🃏 Спец-карта",
        'not_in_game': "⚠️ Ты не в комнате!",
        'not_host': "⚠️ Только хост может запустить игру!",
        'bunker_info': "🏛 **БУНКЕР:** Вместимость 50%.",
        'rules': "📖 **ПРАВИЛА:**\n1. Выживай.\n2. Участвуй в ЧП событиях.\n3. Побеждай!",
        'vote_start': "🗳 **ГОЛОСОВАНИЕ И ЧП НАЧАЛИСЬ!**\nВыберите, кого изгнать:",
        'vote_success': "✅ Голос принят!",
        'vote_already': "⚠️ Ты уже проголосовал!",
        'vote_results': "📊 **РЕЗУЛЬТАТЫ:**\n\n{results}\n\n💀 **Изгнан:** {kicked}"
    },
    'uz': {
        'welcome': "👋 Salom, **{name}**!\n\nTilni tanlang / Выберите язык:",
        'start_menu': "☣️ **«BUNKER» ULTIMATE EDITION** ☣️",
        'btn_create': "➕ Xona yaratish",
        'btn_join': "🚪 Kod bo'yicha kirish",
        'btn_card': "📜 Mening kartam",
        'btn_reveal': "👁 Xususiyatni ochish",
        'btn_profile': "👤 Profil / VIP 🌟",
        'btn_shop': "🛒 Do'kon",
        'btn_vip': "⭐ VIP sotib olish (20 Yulduz)",
        'btn_players': "👥 O'yinchilar",
        'btn_vote': "🗳 Ovoz berish + Fevqulodda vaziyat",
        'btn_start_game': "🚀 O'yinni boshlash (Xost)",
        'btn_disaster': "🌪 Ofat",
        'btn_bunker': "🏛 Bunker",
        'btn_rules': "📖 Qoidalar",
        'btn_lang': "🌐 Til",
        'room_created': "🚨 **XONA YARATILDI!** 🔑 Kod: `{code}`",
        'enter_code': "🔢 Xona kodini kiriting:",
        'room_not_found': "❌ Xona topilmadi.",
        'room_joined': "✅ Siz `#{code}` xonasiga kirdingiz!",
        'game_started_msg': "🚀 **O'YIN BOSHLANDI!**",
        'card_title': "📜 **KARTANGIZ**",
        'prof': "💼 Kasbi",
        'health': "🩺 Sog'lig'i",
        'bio': "🧬 Biologiyasi",
        'hobby': "⚽ Xobbisi",
        'inventory': "🎒 Anjomlari",
        'phobia': "🎭 Fobiya",
        'special': "🃏 Maxsus",
        'not_in_game': "⚠️ Siz xonada emassiz!",
        'not_host': "⚠️ Faqat xost boshlay oladi!",
        'bunker_info': "🏛 **BUNKER:** Sig'imi 50%.",
        'rules': "📖 **QOIDALAR:** Omon qoling!",
        'vote_start': "🗳 **OVOZ BERISH VA FEVQULODDA VAZIYAT!**",
        'vote_success': "✅ Qabul qilindi!",
        'vote_already': "⚠️ Siz ovoz berdingiz!",
        'vote_results': "📊 **NATIJALAR:**\n\n{results}\n\n💀 **Haydalgan:** {kicked}"
    }
}

# --- 5. Генерация карт ---
def generate_survivor_card(lang='ru', is_vip=False):
    if lang == 'uz':
        professions = ["Shifokor 🩺", "Muhandis 🛠", "Oshpaz 🍳", "Militsiya 👮‍♂️", "O'qituvchi 📚", "Dasturchi 💻", "Biolog 🧪", "Fermer 🚜"]
        health_status = ["Mutlaqo sog'lom 💪", "Astma 🫁", "Yengil ko'zoynak 👓", "Changga allergiya 🤧"]
        hobbies = ["Ovchilik 🎯", "Pazandalik 🍲", "Texnika 🔧", "Shaxmat ♟"]
        inventories = ["Dori qutisi 💊", "Miltiq 🔫", "Fonar 🔦", "Suv filtri 🚰"]
        phobias = ["Qorong'ulik 🌙", "Klaustrofobiya 📦", "Optimist 😄"]
        specials = ["Istalganini chiqarish 🃏", "Sog'likni almashtirish 🔄"]
        genders = ["Erkak 👨", "Ayol 👩"]
        repro = ["Farzand ko'ra oladi 👶", "Farzand ko'ra olmaydi ❌"]
    else:
        professions = ["Врач 🩺", "Инженер 🛠", "Повар 🍳", "Полицейский 👮‍♂️", "Учитель 📚", "Программист 💻", "Биолог 🧪", "Фермер 🚜"]
        health_status = ["Идеально здоров 💪", "Астма 🫁", "Близорукость 👓", "Аллергия 🤧"]
        hobbies = ["Охота 🎯", "Кулинария 🍲", "Ремонт 🔧", "Шахматы ♟"]
        inventories = ["Аптечка 💊", "Ружье 🔫", "Фонарь 🔦", "Фильтр 🚰"]
        phobias = ["Темнота 🌙", "Клаустрофобия 📦", "Оптимист 😄"]
        specials = ["Исключить любого 🃏", "Поменяться 🔄"]
        genders = ["Мужчина 👨", "Женщина 👩"]
        repro = ["Плодовит(а) 👶", "Бесплоден(на) ❌"]
    
    health = "Идеально здоров 💪 (VIP бонус)" if is_vip else random.choice(health_status)
    age = random.randint(18, 65)
    gender = random.choice(genders)
    rep = random.choice(repro)
    t = TEXTS[lang]
    
    return {
        t['prof']: random.choice(professions),
        t['health']: health,
        t['bio']: f"{gender}, {age} лет ({rep})" if lang == 'ru' else f"{gender}, {age} yosh ({rep})",
        t['hobby']: random.choice(hobbies),
        t['inventory']: random.choice(inventories),
        t['phobia']: random.choice(phobias),
        t['special']: random.choice(specials)
    }

# --- 6. Клавиатуры ---
def get_language_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
        types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="set_lang_uz")
    )
    return markup

def get_main_keyboard(lang='ru'):
    t = TEXTS[lang]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(t['btn_create']), types.KeyboardButton(t['btn_join']))
    markup.add(types.KeyboardButton(t['btn_card']), types.KeyboardButton(t['btn_reveal']))
    markup.add(types.KeyboardButton(t['btn_profile']), types.KeyboardButton(t['btn_vip']))
    markup.add(types.KeyboardButton(t['btn_shop']), types.KeyboardButton(t['btn_start_game']))
    markup.add(types.KeyboardButton(t['btn_players']), types.KeyboardButton(t['btn_vote']))
    markup.add(types.KeyboardButton(t['btn_disaster']), types.KeyboardButton(t['btn_bunker']))
    markup.add(types.KeyboardButton(t['btn_rules']), types.KeyboardButton(t['btn_lang']))
    return markup

# --- 7. Обработчики ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, TEXTS['ru']['welcome'].format(name=message.from_user.first_name), reply_markup=get_language_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_lang_'))
def set_language(call):
    lang = call.data.split('_')[-1]
    user_languages[call.message.chat.id] = lang
    t = TEXTS[lang]
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, t['start_menu'], reply_markup=get_main_keyboard(lang), parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    lang = user_languages.get(user_id, 'ru')
    t = TEXTS[lang]
    text = message.text

    if user_id not in user_balances:
        user_balances[user_id] = 50
    if user_id not in user_titles:
        user_titles[user_id] = "Новичок 🐣"

    if text in [t['btn_lang'], "🌐 Сменить язык", "🌐 Tilni o'zgartirish", "🌐 Til"]:
        bot.send_message(message.chat.id, "Выбери язык / Tilni tanlang:", reply_markup=get_language_keyboard())
        return

    # ⭐ Покупка VIP
    if text == t['btn_vip']:
        prices = [types.LabeledPrice(label="VIP Статус (Бункер)", amount=20)]
        bot.send_invoice(
            chat_id=message.chat.id,
            title="🌟 VIP Статус в Бункере",
            description="Дает x2 монет, идеальное здоровье и золотой статус!",
            invoice_payload="vip_status_payment",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="vip_buy"
        )
        return

    if text == t['btn_profile']:
        bal = user_balances.get(user_id, 0)
        title = user_titles.get(user_id, "Новичок 🐣")
        vip_status = "✨ АКТИВЕН (VIP)" if user_id in vip_users else "Обычный"
        msg = f"👤 **ПРОФИЛЬ:**\n📝 Имя: {user_name}\n🎖 Титул: {title}\n⭐ VIP: {vip_status}\n💰 Монеты: `{bal}` 🪙"
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
        return

    if text == t['btn_shop']:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("👑 Титул «Легенда» (200 🪙)", callback_data="buy_title_legend"))
        markup.add(types.InlineKeyboardButton("🧟‍♂️ Титул «Охотник» (150 🪙)", callback_data="buy_title_zombie"))
        bot.send_message(message.chat.id, "🛒 **МАГАЗИН:**", reply_markup=markup, parse_mode="Markdown")
        return

    if text == t['btn_bunker']:
        bot.send_message(message.chat.id, t['bunker_info'], parse_mode="Markdown")
        return
    if text == t['btn_rules']:
        bot.send_message(message.chat.id, t['rules'], parse_mode="Markdown")
        return

    if text == t['btn_create']:
        room_code = str(random.randint(1000, 9999))
        disaster = random.choice(DISASTERS_RU if lang == 'ru' else DISASTERS_UZ)
        private_rooms[room_code] = {
            'host': user_id, 'disaster': disaster, 'started': False,
            'players': {user_id: {'name': user_name, 'card': None}}
        }
        players[user_id] = {'room': room_code, 'name': user_name}
        bot.send_message(message.chat.id, t['room_created'].format(code=room_code), reply_markup=get_main_keyboard(lang), parse_mode="Markdown")

    elif text == t['btn_join']:
        user_states[user_id] = 'waiting_room_code'
        bot.send_message(message.chat.id, t['enter_code'])

    elif text == t['btn_start_game']:
        if user_id not in players:
            bot.send_message(message.chat.id, t['not_in_game'])
            return
        room_code = players[user_id]['room']
        room = private_rooms[room_code]
        if room['host'] != user_id:
            bot.send_message(message.chat.id, t['not_host'])
            return

        room['started'] = True
        for pid, pdata in room['players'].items():
            plang = user_languages.get(pid, 'ru')
            is_vip = pid in vip_users
            pdata['card'] = generate_survivor_card(plang, is_vip)
            card_msg = f"{TEXTS[plang]['game_started_msg']}\n\n🌪 **Катастрофа:**\n{room['disaster']}\n\n"
            for k, v in pdata['card'].items():
                card_msg += f"🔹 **{k}:** {v}\n"
            bot.send_message(pid, card_msg, parse_mode="Markdown")

    elif text == t['btn_card']:
        if user_id not in players:
            bot.send_message(message.chat.id, t['not_in_game'])
            return
        room_code = players[user_id]['room']
        pdata = private_rooms[room_code]['players'].get(user_id)
        if not pdata or not pdata['card']:
            bot.send_message(message.chat.id, "⚠️ Игра не начата!")
            return
        card_text = f"{t['card_title']}\n\n"
        for k, v in pdata['card'].items():
            card_text += f"🔹 **{k}:** {v}\n"
        bot.send_message(message.chat.id, card_text, parse_mode="Markdown")

    elif text == t['btn_reveal']:
        if user_id not in players:
            bot.send_message(message.chat.id, t['not_in_game'])
            return
        room_code = players[user_id]['room']
        pdata = private_rooms[room_code]['players'].get(user_id)
        if not pdata or not pdata['card']:
            bot.send_message(message.chat.id, "⚠️ Игра не начата!")
            return
        markup = types.InlineKeyboardMarkup()
        for trait_key in pdata['card'].keys():
            markup.add(types.InlineKeyboardButton(f"📢 Открыть: {trait_key}", callback_data=f"reveal_{room_code}_{trait_key}"))
        bot.send_message(message.chat.id, "Выбери характеристику:", reply_markup=markup)

    elif text == t['btn_players']:
        if user_id not in players:
            bot.send_message(message.chat.id, t['not_in_game'])
            return
        room_code = players[user_id]['room']
        room_players = private_rooms[room_code]['players']
        msg = f"👥 **ИГРОКИ #{room_code}:**\n\n"
        for pid, pdata in room_players.items():
            icon = "👑 " if pid == private_rooms[room_code]['host'] else "👤 "
            vip_icon = "⭐ [VIP] " if pid in vip_users else ""
            msg += f"{vip_icon}{icon}**{pdata['name']}**\n"
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")

    elif text == t['btn_vote']:
        if user_id not in players:
            bot.send_message(message.chat.id, t['not_in_game'])
            return

        room_code = players[user_id]['room']
        room_players = private_rooms[room_code]['players']
        
        # Выбираем случайное ЧП для этого раунда
        current_event = random.choice(EVENTS_RU)
        
        markup = types.InlineKeyboardMarkup()
        for pid, pdata in room_players.items():
            markup.add(types.InlineKeyboardButton(f"💀 Изгнать {pdata['name']}", callback_data=f"vote_{room_code}_{pid}"))
            
        votes[room_code] = {}
        for pid in room_players.keys():
            plang = user_languages.get(pid, 'ru')
            bot.send_message(pid, f"{current_event}\n\n{TEXTS[plang]['vote_start']}", reply_markup=markup, parse_mode="Markdown")

    elif user_states.get(user_id) == 'waiting_room_code':
        room_code = text.strip()
        if room_code in private_rooms:
            private_rooms[room_code]['players'][user_id] = {'name': user_name, 'card': None}
            players[user_id] = {'room': room_code, 'name': user_name}
            user_states[user_id] = None
            bot.send_message(message.chat.id, t['room_joined'].format(code=room_code), parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, t['room_not_found'])

# --- 8. Платежи и Обработчики ---
@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    if message.successful_payment.invoice_payload == "vip_status_payment":
        user_id = message.from_user.id
        vip_users.add(user_id)
        user_titles[user_id] = "🌟 VIP Легенда"
        bot.send_message(message.chat.id, "🎉 Поздравляем! VIP Статус активирован за 20 звёзд! 🌟")

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_title_'))
def process_shop_buy(call):
    user_id = call.from_user.id
    item = call.data.replace('buy_title_', '')
    prices = {'legend': (200, "👑 Легенда Бункера"), 'zombie': (150, "🧟‍♂️ Охотник")}
    cost, title_name = prices.get(item, (9999, ""))
    if user_balances.get(user_id, 0) >= cost:
        user_balances[user_id] -= cost
        user_titles[user_id] = title_name
        bot.answer_callback_query(call.id, f"🎉 Куплен титул: {title_name}!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, f"❌ Не хватает монет! Нужно: {cost} 🪙", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reveal_'))
def process_reveal(call):
    user_id = call.from_user.id
    _, room_code, trait_key = call.data.split('_', 2)
    room = private_rooms.get(room_code)
    if not room or user_id not in room['players']:
        return
    pdata = room['players'][user_id]
    trait_val = pdata['card'].get(trait_key, "???")
    announce = f"📢 **{pdata['name']}** раскрыл характеристику:\n🔹 **{trait_key}:** {trait_val}"
    for pid in room['players'].keys():
        bot.send_message(pid, announce, parse_mode="Markdown")
    bot.answer_callback_query(call.id, "Раскрыто!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('vote_'))
def process_vote(call):
    voter_id = call.from_user.id
    _, room_code, target_id = call.data.split('_')
    target_id = int(target_id)
    if room_code not in private_rooms:
        return
    if room_code not in votes:
        votes[room_code] = {}

    if voter_id in votes[room_code]:
        bot.answer_callback_query(call.id, "Вы уже проголосовали!", show_alert=True)
        return

    votes[room_code][voter_id] = target_id
    bot.answer_callback_query(call.id, "Голос принят!")
    
    room_players = private_rooms[room_code]['players']
    if len(votes[room_code]) >= len(room_players):
        tally = {}
        for voted_target in votes[room_code].values():
            tally[voted_target] = tally.get(voted_target, 0) + 1
            
        kicked_id = max(tally, key=tally.get)
        kicked_name = room_players[kicked_id]['name']
        
        results_text = ""
        for pid, pdata in room_players.items():
            count = tally.get(pid, 0)
            results_text += f"👤 **{pdata['name']}**: {count} голосов\n"
            multiplier = 2 if pid in vip_users else 1
            if pid != kicked_id:
                user_balances[pid] = user_balances.get(pid, 0) + (100 * multiplier)
            else:
                user_balances[pid] = user_balances.get(pid, 0) + (20 * multiplier)
            
        for pid in room_players.keys():
            plang = user_languages.get(pid, 'ru')
            pt = TEXTS[plang]
            msg = pt['vote_results'].format(results=results_text, kicked=kicked_name)
            bot.send_message(pid, msg, parse_mode="Markdown")

# --- 9. Запуск ---
if __name__ == "__main__":
    print("Бот Бункер Ultimate запущен!")
    bot.remove_webhook()
    bot.infinity_polling()
