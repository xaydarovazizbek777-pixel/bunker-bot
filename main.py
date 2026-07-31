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
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask).start()

# --- 2. Инициализация Бота ---
TOKEN = "8963766433:AAFX8f3AW0IuHq_BDBVPhgU482gB2fJ1N4o"
bot = telebot.TeleBot(TOKEN)

# Хранилища
private_rooms = {} 
user_states = {}   
players = {}       
user_languages = {} 

# --- 3. Тексты на разных языках ---
TEXTS = {
    'ru': {
        'welcome': "👋 Привет, {name}!\n\nВыбери язык / Tilni tanlang:",
        'start_menu': "Ты попал в систему выживания **Бункер** ☣️\nИспользуй кнопки ниже для игры!",
        'btn_create': "➕ Создать комнату",
        'btn_join': "🚪 Войти по коду",
        'btn_card': "🎲 Моя карта выжившего",
        'btn_bunker': "🏛 Описание Бункера",
        'btn_rules': "📖 Правила игры",
        'btn_lang': "🌐 Сменить язык",
        'room_created': "🏁 Игра #{code} создана!\nКод комнаты: `{code}`\nПередай этот код друзьям!",
        'enter_code': "🔢 Введи 4-значный код комнаты:",
        'room_not_found': "❌ Комната с таким кодом не найдена.",
        'room_joined': "✅ Ты успешно вошел в комнату #{code}!",
        'card_title': "👤 **ТВОЯ КАРТА ВЫЖИВШЕГО**",
        'prof': "💼 Профессия",
        'health': "🩺 Здоровье",
        'bio': "🧬 Биология",
        'hobby': "⚽ Хобби",
        'inventory': "🎒 Багаж",
        'phobia': "🎭 Фобия / Характер",
        'special': "🃏 Спец-карта",
        'not_in_game': "Ты не в игре!",
        'bunker_info': "☣️ **КАТАСТРОФА:** На Земле произошёл ядерный апокалипсис.\n\n🏛 **БУНКЕР:**\n- Вместимость: 50% от числа выживших.\n- Запасы еды: на 1 год.\n- Оборудование: Гидропоника, фильтры воздуха.\n\nВаша задача — убедить остальных, что именно вы должны попасть в бункер!",
        'rules': "📖 **ПРАВИЛА ИГРЫ:**\n1. Каждый игрок получает уникальную карту выжившего.\n2. По очереди открывайте свои характеристики и доказывайте свою пользу для бункера.\n3. В конце каждого раунда проходит голосование — один игрок изгоняется.\n4. Выигрывают те, кто останется в бункере до конца!"
    },
    'uz': {
        'welcome': "👋 Salom, {name}!\n\nTilni tanlang / Выберите язык:",
        'start_menu': "Siz **Bunker** omon qolish tizimiga kirdingiz ☣️\nO'ynash uchun pastdagi tugmalardan foydalaning!",
        'btn_create': "➕ Xona yaratish",
        'btn_join': "🚪 Kod bo'yicha kirish",
        'btn_card': "🎲 Mening kartam",
        'btn_bunker': "🏛 Bunker haqida",
        'btn_rules': "📖 O'yin qoidalari",
        'btn_lang': "🌐 Tilni o'zgartirish",
        'room_created': "🏁 #{code} o'yini yaratildi!\nXona kodi: `{code}`\nUshbu kodni do'stlaringizga yuboring!",
        'enter_code': "🔢 4 xonali xona kodini kiriting:",
        'room_not_found': "❌ Bunday kodli xona topilmadi.",
        'room_joined': "✅ Siz #{code} xonasiga muvaffaqiyatli kirdingiz!",
        'card_title': "👤 **SIZNING OMON QOLUVCHI KARTANGIZ**",
        'prof': "💼 Kasbi",
        'health': "🩺 Sog'lig'i",
        'bio': "🧬 Biologiyasi",
        'hobby': "⚽ Xobbisi",
        'inventory': "🎒 Anjomlari",
        'phobia': "🎭 Fobiya / Xarakter",
        'special': "🃏 Maxsus karta",
        'not_in_game': "Siz o'yinda emassiz!",
        'bunker_info': "☣️ **OFAT:** Yer yuzida yadroviy apokalipsis yuz berdi.\n\n🏛 **BUNKER:**\n- Siqimi: Omon qolganlarning 50 foizi.\n- Oziq-ovqat zaxirasi: 1 yilga mo'ljallangan.\n\nVazifangiz — bunkerga aynan siz kirishingiz kerakligini boshqalarga isbotlash!",
        'rules': "📖 **O'YIN QOIDALARI:**\n1. Har bir o'yinchi maxsus karta oladi.\n2. Navbat bilan kartangizdagi xususiyatlarni ochib, foydangizni isbotlang.\n3. Har bir raund oxirida ovoz berish o'tkaziladi va bir kishi chiqarib yuboriladi."
    }
}

# --- 4. Расширенная генерация карт ---
def generate_survivor_card(lang='ru'):
    if lang == 'uz':
        professions = ["Shifokor", "Muhandis", "Oshpaz", "Militsiya", "O'qituvchi", "Dasturchi", "Elektrik", "Quruvchi", "Biolog", "Fermer"]
        health_status = ["Mutlaqo sog'lom", "Astma", "Yengil uzoqni ko me'yor", "Changga allergiya", "Uyqusizlik", "Qandli diabet"]
        hobbies = ["Ovchilik", "Pazandalik", "Texnika ta'mirlash", "O'rmonda omon qolish", "Shaxmat", "Yugurish", "Kitob o'qish"]
        inventories = ["Dori-darmon qutisi", "Ov miltig'i", "Fonaik va batareyalar", "Suv filtri", "Urug'lar toplami", "Konserva qush qutisi"]
        phobias = ["Qorong'ulikdan qo'rqish", "Klaustrofobiya (tor joy)", "Paranoi baseline", "Optimist", "Agressiv"]
        specials = ["Istalgan o'yinchini chiqarib yuborish", "Sog'likni boshqasi bilan almashtirish", "Ovoz berishni bekor qilish"]
        genders = ["Erkak", "Ayol"]
        repro = ["Beshik tebrata oladi", "Beshik tebrata olmaydi"]
    else:
        professions = ["Врач", "Инженер", "Повар", "Полицейский", "Учитель", "Программист", "Электрик", "Строитель", "Биолог", "Фермер"]
        health_status = ["Идеально здоров", "Астма", "Легкая близорукость", "Аллергия на пыль", "Бессонница", "Сахарный диабет"]
        hobbies = ["Охота", "Кулинария", "Ремонт техники", "Выживание в лесу", "Шахматы", "Бег", "Чтение книг"]
        inventories = ["Аптечка", "Охотничье ружье", "Фонарь и батарейки", "Фильтр для воды", "Набор семян", "Ящик консервов"]
        phobias = ["Боязнь темноты", "Клаустрофобия", "Паранойя", "Оптимист", "Агрессивный"]
        specials = ["Исключить любого игрока", "Поменяться здоровьем с другом", "Отменить результаты голосования"]
        genders = ["Мужчина", "Женщина"]
        repro = ["Плодовит(а)", "Бесплоден(на)"]
    
    age = random.randint(18, 65)
    gender = random.choice(genders)
    rep = random.choice(repro)
    t = TEXTS[lang]
    
    return {
        t['prof']: random.choice(professions),
        t['health']: random.choice(health_status),
        t['bio']: f"{gender}, {age} лет ({rep})" if lang == 'ru' else f"{gender}, {age} yosh ({rep})",
        t['hobby']: random.choice(hobbies),
        t['inventory']: random.choice(inventories),
        t['phobia']: random.choice(phobias),
        t['special']: random.choice(specials)
    }

# --- 5. Клавиатуры ---
def get_language_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn_ru = types.InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru")
    btn_uz = types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="set_lang_uz")
    markup.add(btn_ru, btn_uz)
    return markup

def get_main_keyboard(lang='ru'):
    t = TEXTS[lang]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton(t['btn_create'])
    btn2 = types.KeyboardButton(t['btn_join'])
    btn3 = types.KeyboardButton(t['btn_card'])
    btn4 = types.KeyboardButton(t['btn_bunker'])
    btn5 = types.KeyboardButton(t['btn_rules'])
    btn6 = types.KeyboardButton(t['btn_lang'])
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    return markup

# --- 6. Обработчики ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        TEXTS['ru']['welcome'].format(name=message.from_user.first_name),
        reply_markup=get_language_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_lang_'))
def set_language(call):
    lang = call.data.split('_')[-1]
    user_languages[call.message.chat.id] = lang
    t = TEXTS[lang]
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(
        call.message.chat.id,
        t['start_menu'],
        reply_markup=get_main_keyboard(lang),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ru')
    t = TEXTS[lang]
    text = message.text

    # Смена языка
    if text in [t['btn_lang'], "🌐 Сменить язык", "🌐 Tilni o'zgartirish"]:
        bot.send_message(message.chat.id, "Выбери язык / Tilni tanlang:", reply_markup=get_language_keyboard())
        return

    # Описание бункера
    if text == t['btn_bunker']:
        bot.send_message(message.chat.id, t['bunker_info'], parse_mode="Markdown")
        return

    # Правила
    if text == t['btn_rules']:
        bot.send_message(message.chat.id, t['rules'], parse_mode="Markdown")
        return

    # ➕ Создание комнаты
    if text == t['btn_create']:
        room_code = str(random.randint(1000, 9999))
        card = generate_survivor_card(lang)
        
        private_rooms[room_code] = {'host': user_id, 'players': {user_id: card}}
        players[user_id] = {'room': room_code, 'card': card}
        
        card_text = f"{t['room_created'].format(code=room_code)}\n\n{t['card_title']}\n\n"
        for k, v in card.items():
            card_text += f"🔹 **{k}:** {v}\n"

        bot.send_message(message.chat.id, card_text, reply_markup=get_main_keyboard(lang), parse_mode="Markdown")

    # 🚪 Войти по коду
    elif text == t['btn_join']:
        user_states[user_id] = 'waiting_room_code'
        bot.send_message(message.chat.id, t['enter_code'])

    # 🎲 Карта выжившего
    elif text == t['btn_card']:
        if user_id in players:
            card = players[user_id]['card']
        else:
            card = generate_survivor_card(lang)
            
        card_text = f"{t['card_title']}\n\n"
        for k, v in card.items():
            card_text += f"🔹 **{k}:** {v}\n"
        bot.send_message(message.chat.id, card_text, parse_mode="Markdown")

    # Ввод кода комнаты
    elif user_states.get(user_id) == 'waiting_room_code':
        room_code = text.strip()
        if room_code in private_rooms:
            card = generate_survivor_card(lang)
            private_rooms[room_code]['players'][user_id] = card
            players[user_id] = {'room': room_code, 'card': card}
            user_states[user_id] = None
            
            card_text = f"{t['room_joined'].format(code=room_code)}\n\n{t['card_title']}\n\n"
            for k, v in card.items():
                card_text += f"🔹 **{k}:** {v}\n"
                
            bot.send_message(message.chat.id, card_text, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, t['room_not_found'])
