import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------- CONFIG ----------------
BOT_TOKEN = "8906381412:AAFKCOhY4pALcJ-FggytPaJWx2qlbcJZGQw"

ADMIN_IDS = [5435444673, 6176631114]

CARD_NUMBER = "5614 6803 7053 0525"
CARD_HOLDER = "R S"

BANNER_URL = "https://i.postimg.cc/85z1XyB1/sotib-olish.jpg"  

PACKAGES = {
    "50": {"stars": 50, "price": "14 000 UZS"},
    "75": {"stars": 75, "price": "18 000 UZS"},
    "100": {"stars": 100, "price": "25 000 UZS"},
    "150": {"stars": 150, "price": "38 000 UZS"},
    "200": {"stars": 200, "price": "50 000 UZS"},
    "250": {"stars": 250, "price": "62 000 UZS"},
    "300": {"stars": 300, "price": "75 000 UZS"},
    "350": {"stars": 350, "price": "88 000 UZS"},
    "400": {"stars": 400, "price": "100 000 UZS"},
    "450": {"stars": 450, "price": "114 000 UZS"},
    "500": {"stars": 500, "price": "125 000 UZS"},
    "600": {"stars": 600, "price": "150 000 UZS"},
    "750": {"stars": 750, "price": "188 000 UZS"},
    "1000": {"stars": 1000, "price": "250 000 UZS"},
}

TEXTS = {
    "uz": {
        "select_lang": "🌐 Tilni tanlang / Выберите язык:",
        "catalog_title": "🌟 **Necha stars sotib olmoqchisiz?**\n\n• **Minimal:** 50 ta\n• **Katta hajmda chegirmalar bor!**\n\n👇 Kerakli paketni tanlang:",
        "support_btn": "ℹ️ Yordam / Qo'llab-quvvatlash",
        "lang_btn": "🌐 Tilni o'zgartirish",
        "enter_username": "Siz tanladingiz: **🌟 {stars} Stars** ({price})\n\n✍️ Stars qabul qiluvchining `@username` nikini yuboring:",
        "payment_info": (
            "📌 **To'lov rekvizitlari:**\n\n"
            "💳 Karta: `{card}`\n"
            "👤 Egasining ismi: {holder}\n"
            "💰 To'lov summasi: **{price}**\n\n"
            "🎯 Qabul qiluvchi: @{target}\n"
            "🌟 Paket: {stars} Stars\n\n"
            "📸 **To'lov chekini (skrinshot) ushbu xabarga yuboring.**"
        ),
        "receipt_received": "✅ **Chek qabul qilindi! Buyurtma #{order_id} yaratildi.**\nAdministrator to'lovni tekshirib, stars yuboradi.",
        "support_text": "💬 Savollar va yordam uchun admin bilan bog'laning: @Shokh_r",
        "order_completed": "✅ **Buyurtma #{order_id} bajarildi!**\n🌟 {stars} Stars @{target} hisobiga o'tkazildi.\nRahmat!",
        "order_rejected": "❌ **Buyurtma #{order_id} rad etildi.**\nXatolik bo'lsa admin bilan bog'laning."
    },
    "ru": {
        "select_lang": "🌐 Выберите язык / Tilni tanlang:",
        "catalog_title": "🌟 **Сколько Stars вы хотите купить?**\n\n• **Минимально:** 50 шт\n• **Скидки при оптовой покупке!**\n\n👇 Выберите нужный пакет:",
        "support_btn": "ℹ️ Помощь / Поддержка",
        "lang_btn": "🌐 Сменить язык",
        "enter_username": "Вы выбрали: **🌟 {stars} Stars** ({price})\n\n✍️ Отправьте `@username` получателя Stars:",
        "payment_info": (
            "📌 **Реквизиты для оплаты:**\n\n"
            "💳 Карта: `{card}`\n"
            "👤 Получатель: {holder}\n"
            "💰 Сумма к оплате: **{price}**\n\n"
            "🎯 Получатель: @{target}\n"
            "🌟 Пакет: {stars} Stars\n\n"
            "📸 **Отправьте чек (скриншот) оплаты в ответ на это сообщение.**"
        ),
        "receipt_received": "✅ **Чек получен! Заказ #{order_id} создан.**\nАдминистратор проверит оплату и отправит Stars.",
        "support_text": "💬 По всем вопросам и поддержке обращайтесь к админу: @Shokh_r",
        "order_completed": "✅ **Заказ #{order_id} выполнен!**\n🌟 {stars} Stars отправлены на аккаунт @{target}.\nСпасибо!",
        "order_rejected": "❌ **Заказ #{order_id} откланен.**\nЕсли есть вопросы, свяжитесь с админом."
    }
}

orders = {}
order_counter = 1000

logging.basicConfig(level=logging.INFO)

# ---------------- HELPERS ----------------

def get_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("lang", "uz")

async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    t = TEXTS[lang]

    keyboard = []
    keys = list(PACKAGES.keys())
    for i in range(0, len(keys), 2):
        row = []
        item1 = PACKAGES[keys[i]]
        row.append(InlineKeyboardButton(f"🌟 {item1['stars']} ⭐ => {item1['price']}", callback_data=f"pkg_{keys[i]}"))
        if i + 1 < len(keys):
            item2 = PACKAGES[keys[i+1]]
            row.append(InlineKeyboardButton(f"🌟 {item2['stars']} ⭐ => {item2['price']}", callback_data=f"pkg_{keys[i+1]}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(t["support_btn"], callback_data="support")])
    keyboard.append([InlineKeyboardButton(t["lang_btn"], callback_data="change_lang")])

    caption = t["catalog_title"]

    if update.callback_query:
        msg = update.callback_query.message
        if BANNER_URL and msg.photo:
            await msg.edit_caption(
                caption=caption,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return
        await msg.reply_text(caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        if BANNER_URL:
            try:
                await update.message.reply_photo(
                    photo=BANNER_URL,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                return
            except Exception:
                pass
        await update.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ---------------- HANDLERS ----------------

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="set_lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru")
        ]
    ])
    await update.message.reply_text("🌐 Tilni tanlang / Выберите язык:", reply_markup=keyboard)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("set_lang_"):
        lang = data.split("_")[2]
        context.user_data["lang"] = lang
        await show_catalog(update, context)

    elif data == "change_lang":
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="set_lang_uz"),
                InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru")
            ]
        ])
        await query.message.reply_text("🌐 Tilni tanlang / Выберите язык:", reply_markup=keyboard)

    elif data.startswith("pkg_"):
        lang = get_lang(context)
        t = TEXTS[lang]
        pkg_key = data.split("_")[1]
        pkg = PACKAGES.get(pkg_key)
        if not pkg:
            return

        context.user_data["selected_pkg"] = pkg_key
        context.user_data["state"] = "WAITING_FOR_USERNAME"

        await query.message.reply_text(
            t["enter_username"].format(stars=pkg['stars'], price=pkg['price']),
            parse_mode="Markdown"
        )

    elif data == "support":
        lang = get_lang(context)
        t = TEXTS[lang]
        await query.message.reply_text(t["support_text"], parse_mode="Markdown")

    elif data.startswith("adm_confirm_"):
        order_id = int(data.split("_")[2])
        order = orders.get(order_id)
        if order:
            order["status"] = "completed"
            user_lang = order.get("lang", "uz")
            t = TEXTS[user_lang]
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=t["order_completed"].format(order_id=order_id, stars=order['stars'], target=order['target_username']),
                parse_mode="Markdown"
            )
            await query.edit_message_caption(
                caption=query.message.caption + f"\n\n✅ **BAJARILDI / ВЫПОЛНЕНО**"
            )

    elif data.startswith("adm_reject_"):
        order_id = int(data.split("_")[2])
        order = orders.get(order_id)
        if order:
            order["status"] = "rejected"
            user_lang = order.get("lang", "uz")
            t = TEXTS[user_lang]
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=t["order_rejected"].format(order_id=order_id),
                parse_mode="Markdown"
            )
            await query.edit_message_caption(
                caption=query.message.caption + f"\n\n❌ **RAD ETILDI / ОТКЛОНЕНО**"
            )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")
    lang = get_lang(context)
    t = TEXTS[lang]

    if state == "WAITING_FOR_USERNAME":
        target = update.message.text.strip().replace("@", "")
        pkg_key = context.user_data.get("selected_pkg")
        pkg = PACKAGES[pkg_key]

        context.user_data["target_username"] = target
        context.user_data["state"] = "WAITING_FOR_RECEIPT"

        text = t["payment_info"].format(
            card=CARD_NUMBER,
            holder=CARD_HOLDER,
            price=pkg['price'],
            target=target,
            stars=pkg['stars']
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    elif state == "WAITING_FOR_RECEIPT" and (update.message.photo or update.message.document):
        global order_counter
        order_counter += 1
        order_id = order_counter

        pkg_key = context.user_data.get("selected_pkg")
        pkg = PACKAGES[pkg_key]
        target = context.user_data.get("target_username")
        user = update.effective_user

        orders[order_id] = {
            "user_id": user.id,
            "username": user.username,
            "target_username": target,
            "stars": pkg["stars"],
            "price": pkg["price"],
            "status": "pending",
            "lang": lang
        }

        context.user_data["state"] = None

        await update.message.reply_text(
            t["receipt_received"].format(order_id=order_id),
            parse_mode="Markdown"
        )

        adm_text = (
            f"📥 **YANGI BUYURTMA / НОВЫЙ ЗАКАЗ #{order_id}**\n\n"
            f"👤 Xaridor / Покупатель: [{user.first_name}](tg://user?id={user.id}) (@{user.username or 'yoq'})\n"
            f"🎯 Kimga / Кому: @{target}\n"
            f"🌟 Paket / Пакет: **{pkg['stars']} Stars**\n"
            f"💰 Summa / Сумма: **{pkg['price']}**\n"
            f"🌐 Til / Язык: {lang.upper()}"
        )
        adm_kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Bajarildi / Принять", callback_data=f"adm_confirm_{order_id}"),
                InlineKeyboardButton("❌ Rad etish / Отклонить", callback_data=f"adm_reject_{order_id}")
            ]
        ])

        for admin_id in ADMIN_IDS:
            try:
                if update.message.photo:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=update.message.photo[-1].file_id,
                        caption=adm_text,
                        reply_markup=adm_kb,
                        parse_mode="Markdown"
                    )
                elif update.message.document:
                    await context.bot.send_document(
                        chat_id=admin_id,
                        document=update.message.document.file_id,
                        caption=adm_text,
                        reply_markup=adm_kb,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logging.error(f"Error admin notification: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.DOCUMENT, message_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
