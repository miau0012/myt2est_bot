import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# აქ ჩაწერე შენი ბოტის ტოკენი ბრჭყალებში
BOT_TOKEN = "7731624807:AAHBuLekFd_hx3N3VJrjnapp2UhhE3jDXWU"

# აქ ჩაწერე შენი ადმინისტრატორის ჩათ აიდი ბრჭყალებში
ADMIN_CHAT_ID = "923742119"

# მომხმარებელთა ID-ების შესანახი ფაილი
CHAT_IDS_FILE = "chat_ids.txt"

# ველოსიპედების ტიპები
bikes = [
    "მთაგორიანი ველო",
    "გზის ველო",
    "BMX ველო",
    "ქალაქის ველო",
    "ელექტრო ველო"
]

# დოკუმენტის შესანახი ID
saved_file_id = None

def save_chat_id(chat_id: int):
    """მომხმარებლის ID-ის შენახვა ფაილში"""
    if not os.path.exists(CHAT_IDS_FILE):
        with open(CHAT_IDS_FILE, "w", encoding="utf-8") as f:
            pass
    with open(CHAT_IDS_FILE, "r+", encoding="utf-8") as f:
        ids = set(line.strip() for line in f if line.strip())
        if str(chat_id) not in ids:
            f.write(f"{chat_id}\n")

def load_chat_ids():
    """მომხმარებელთა ID-ების ჩატვირთვა"""
    if not os.path.exists(CHAT_IDS_FILE):
        return set()
    with open(CHAT_IDS_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ბოტის დაწყების ფუნქცია"""
    user = update.message.from_user
    chat_id = update.message.chat.id
    save_chat_id(chat_id)

    keyboard = [
        [InlineKeyboardButton("🚲 ველოსიპედის ქირაობა", callback_data="rent_bike")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("მოგესალმებით! აირჩიეთ ველოსიპედის ქირაობა:", reply_markup=reply_markup)

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"🆕 ახალი მომხმარებელი:\n👤 {user.full_name}\n🆔 @{user.username or 'არა'}\n#️⃣ {chat_id}"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ღილაკების დამუშავება"""
    global saved_file_id
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user
    chat_id = query.message.chat.id
    save_chat_id(chat_id)

    if data == "rent_bike":
        keyboard = [[InlineKeyboardButton(bike, callback_data=f"bike_{i}")] for i, bike in enumerate(bikes)]
        keyboard.append([InlineKeyboardButton("🔙 უკან", callback_data="back_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🚴 აირჩიეთ ველოსიპედის ტიპი:", reply_markup=reply_markup)

    elif data.startswith("bike_"):
        bike_index = int(data.split("_")[1])
        bike_name = bikes[bike_index]
        
        keyboard = [
            [InlineKeyboardButton("✅ დადასტურება", callback_data=f"confirm_{bike_index}")],
            [InlineKeyboardButton("❌ გაუქმება", callback_data="rent_bike")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🚲 თქვენ აირჩიეთ: {bike_name}\n\n"
            "გთხოვთ დაადასტუროთ ქირაობა:",
            reply_markup=reply_markup
        )

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"🚴 მომხმარებელმა აირჩია ველოსიპედი:\n"
                 f"👤 {user.full_name} (@{user.username})\n"
                 f"🆔 {chat_id}\n"
                 f"🚲 {bike_name}"
        )

    elif data.startswith("confirm_"):
        bike_index = int(data.split("_")[1])
        bike_name = bikes[bike_index]
        
        await query.edit_message_text(
            f"🎉 გმადლობთ! {bike_name} წარმატებით გაქირავდით.\n\n"
            "ჩვენი მენეჯერი მალე დაგიკავშირდებათ დეტალების გასარკვევად."
        )

        if saved_file_id:
            try:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=saved_file_id,
                    caption="📄 ქირაობის წესები და პირობები"
                )
            except Exception:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ დოკუმენტის გაგზავნა ვერ მოხერხდა. გთხოვთ დაგვიკავშირდეთ."
                )

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"✅ ქირაობა დადასტურებულია:\n"
                 f"👤 {user.full_name}\n"
                 f"🆔 {chat_id}\n"
                 f"🚲 {bike_name}\n\n"
                 f"გთხოვთ დაუკავშირდეთ მომხმარებელს."
        )

    elif data == "back_main":
        await start(update, context)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """დოკუმენტის მიღება ადმინისტრატორისგან"""
    global saved_file_id
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ ამ ფუნქციის გამოყენება მხოლოდ ადმინისტრატორს შეუძლია.")
        return

    document = update.message.document
    if document:
        saved_file_id = document.file_id
        await update.message.reply_text(
            f"📄 დოკუმენტი შენახულია!\n"
            f"ფაილის ID: {saved_file_id}\n"
            f"ახლა მომხმარებლებს შეეძლებათ მისი მიღება ქირაობის დადასტურებისას."
        )

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """მომხმარებლის შეტყობინებების ადმინისტრატორთან გადაგზავნა"""
    if str(update.effective_chat.id) == ADMIN_CHAT_ID:
        return

    user = update.message.from_user
    save_chat_id(update.effective_chat.id)

    try:
        await context.bot.forward_message(
            chat_id=ADMIN_CHAT_ID,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
    except Exception as e:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"⚠️ შეცდომა შეტყობინების გადაგზავნისას:\n{str(e)}"
        )

async def admin_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ადმინისტრატორის გაგზავნის ფუნქცია (/send)"""
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ ამ ბრძანების გამოყენება მხოლოდ ადმინისტრატორს შეუძლია.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("ℹ️ გამოყენება: /send <chat_id> <შეტყობინება>")
        return

    target_id = context.args[0]
    message = " ".join(context.args[1:])

    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=f"📩 ადმინისტრატორისგან:\n\n{message}"
        )
        await update.message.reply_text("✅ შეტყობინება წარმატებით გაიგზავნა.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ შეცდომა: {str(e)}")

async def admin_replay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ადმინისტრატორის საპასუხო ფუნქცია (/replay)"""
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ ამ ბრძანების გამოყენება მხოლოდ ადმინისტრატორს შეუძლია.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("ℹ️ გამოყენება: /replay <chat_id> <შეტყობინება>")
        return

    target_id = context.args[0]
    message = " ".join(context.args[1:])

    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=message
        )
        await update.message.reply_text("✅ შეტყობინება წარმატებით გაიგზავნა.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ შეცდომა: {str(e)}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", admin_send))
    app.add_handler(CommandHandler("replay", admin_replay))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_to_admin))

    app.run_polling()
