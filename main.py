import os
import json
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes
)

TOKEN = os.getenv("TOKEN")  # Setează în Render ca Environment Variable
WARNS_FILE = "warns.json"

# ====== UTILITARE =====

def load_warns():
    if not os.path.exists(WARNS_FILE):
        return {}
    with open(WARNS_FILE, "r") as f:
        return json.load(f)

def save_warns(warns):
    with open(WARNS_FILE, "w") as f:
        json.dump(warns, f)

def cleanup_warns(warns):
    now = datetime.utcnow()
    for user_id in list(warns):
        warns[user_id] = [w for w in warns[user_id] if datetime.fromisoformat(w["date"]) + timedelta(days=30) > now]
        if not warns[user_id]:
            del warns[user_id]
    return warns

# ====== COMENZI =====

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Dă reply la un mesaj ca să avertizezi.")
        return

    reason = " ".join(context.args) if context.args else "Fără motiv"
    warns = load_warns()
    user_id = str(update.message.reply_to_message.from_user.id)

    warns.setdefault(user_id, []).append({
        "reason": reason,
        "date": datetime.utcnow().isoformat()
    })

    warns = cleanup_warns(warns)
    save_warns(warns)

    count = len(warns[user_id])
    await update.message.reply_text(f"🚨 Avertisment pentru {update.message.reply_to_message.from_user.first_name}.\nMotiv: {reason}\nTotal: {count}/3")

    if count >= 3:
        await update.message.chat.ban_member(user_id)
        await update.message.reply_text(f"{update.message.reply_to_message.from_user.first_name} a fost banat pentru 3 avertismente.")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or len(context.args) < 1:
        await update.message.reply_text("Folosire: /mute <minute> <motiv> (cu reply)")
        return

    try:
        minutes = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Timp invalid.")
        return

    until_date = datetime.utcnow() + timedelta(minutes=minutes)
    await update.message.chat.restrict_member(
        user_id=update.message.reply_to_message.from_user.id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until_date
    )
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Fără motiv"
    await update.message.reply_text(f"{update.message.reply_to_message.from_user.first_name} a fost mutat pentru {minutes} minute.\nMotiv: {reason}")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Dă reply la un mesaj ca să banezi.")
        return
    await update.message.chat.ban_member(update.message.reply_to_message.from_user.id)
    await update.message.reply_text("Utilizator banat.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot activ și funcțional!")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("warn", warn))
    application.add_handler(CommandHandler("mute", mute))
    application.add_handler(CommandHandler("ban", ban))

    application.run_polling()

if __name__ == "__main__":
    main()
