
import json
import os
import time
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "PUNE_AICI_TOKENUL_TAU"
WARN_FILE = "warns.json"

def load_warns():
    if os.path.exists(WARN_FILE):
        with open(WARN_FILE, "r") as f:
            return json.load(f)
    return {}

def save_warns(warns):
    with open(WARN_FILE, "w") as f:
        json.dump(warns, f, indent=2)

def clean_old_warns(warns):
    now = time.time()
    for user_id in list(warns.keys()):
        warns[user_id] = [w for w in warns[user_id] if now - w["timestamp"] < 30 * 24 * 3600]
        if not warns[user_id]:
            del warns[user_id]
    return warns

async def is_admin(update: Update, user_id: int):
    member = await update.effective_chat.get_member(user_id)
    return member.status in ("administrator", "creator")

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, update.effective_user.id):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Trebuie să dai reply la mesajul utilizatorului.")
        return

    reason = " ".join(context.args) if context.args else "Fără motiv"
    target = update.message.reply_to_message.from_user
    warns = load_warns()
    warns = clean_old_warns(warns)
    user_id = str(target.id)

    if user_id not in warns:
        warns[user_id] = []

    warns[user_id].append({
        "reason": reason,
        "timestamp": time.time()
    })
    save_warns(warns)

    warn_count = len(warns[user_id])
    if warn_count >= 3:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, target.id)
            await update.message.reply_text(f"{target.mention_html()} a primit 3/3 warnuri și a fost banat.", parse_mode="HTML")
        except:
            await update.message.reply_text("❌ Nu am putut bana acest membru.")
    else:
        await update.message.reply_text(f"{target.mention_html()} a primit warn {warn_count}/3. Motiv: {reason}", parse_mode="HTML")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, update.effective_user.id):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Trebuie să dai reply la mesajul utilizatorului.")
        return

    reason = " ".join(context.args) if context.args else "Fără motiv"
    target = update.message.reply_to_message.from_user

    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"{target.mention_html()} a fost banat. Motiv: {reason}", parse_mode="HTML")
    except:
        await update.message.reply_text("❌ Nu am putut bana acest membru.")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, update.effective_user.id):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Trebuie să dai reply la mesajul utilizatorului.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Folosește: /mute minute motiv")
        return

    try:
        minutes = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Fără motiv"
    except:
        await update.message.reply_text("Timpul trebuie să fie un număr.")
        return

    until_date = datetime.utcnow() + timedelta(minutes=minutes)
    target = update.message.reply_to_message.from_user

    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target.id,
            ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await update.message.reply_text(f"{target.mention_html()} a primit mute pentru {minutes} minute. Motiv: {reason}", parse_mode="HTML")
    except:
        await update.message.reply_text("❌ Nu am putut da mute acestui membru.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("mute", mute))
    print("🤖 Botul pe reply rulează.")
    app.run_polling()

if __name__ == "__main__":
    main()
