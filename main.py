
import json
import os
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    filters, CallbackContext
)

TOKEN = os.getenv("BOT_TOKEN")  # Trebuie setat în Render ca Environment Variable

WARNS_FILE = "warns.json"

# ====== UTILITARE ======

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

# ====== COMENZI ======

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Botul este activ și gata de acțiune!")

async def reguli(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
📜 *Regulament General*:

1. Fără limbaj vulgar – se poate sancționa cu *mute pe termen nedeterminat*.
2. Sistem de avertismente (*warn*): 3/3 = *ban automat*. Fiecare warn expiră în 30 de zile.
3. Este *interzisă reclama* la alte grupuri, documente false, droguri, pariuri etc.
4. Respectați ceilalți membri. Grupul este pentru ajutor și colaborare.
5. Nu oferiți informații personale necunoscuților. Fiți vigilenți în discuții.

Pentru orice problemă, contactați un admin.
"""
    await update.message.reply_markdown(text)

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("Folosește comanda ca reply la mesaj.")

    if not await is_admin(update):
        return

    user = update.message.reply_to_message.from_user
    motive = " ".join(context.args) or "Fără motiv"
    warns = load_warns()

    user_id = str(user.id)
    warns.setdefault(user_id, [])
    warns[user_id].append({"date": datetime.utcnow().isoformat(), "reason": motive})

    warns = cleanup_warns(warns)
    save_warns(warns)

    if len(warns[user_id]) >= 3:
        await update.effective_chat.ban_member(user.id)
        await update.message.reply_text(f"{user.mention_html()} a fost banat pentru acumularea a 3/3 warnuri.", parse_mode="HTML")
        del warns[user_id]
        save_warns(warns)
    else:
        await update.message.reply_text(f"{user.mention_html()} a primit warn pentru: *{motive}*. ({len(warns[user_id])}/3)", parse_mode="HTML")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("Folosește comanda ca reply la mesaj.")

    if not await is_admin(update):
        return

    user = update.message.reply_to_message.from_user
    if len(context.args) < 1:
        return await update.message.reply_text("Folosește: /mute minute motiv")

    try:
        minutes = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("Primul argument trebuie să fie un număr (minute).")

    motive = " ".join(context.args[1:]) or "Fără motiv"
    until = datetime.utcnow() + timedelta(minutes=minutes)
    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        user.id,
        ChatPermissions(can_send_messages=False),
        until_date=until
    )
    await update.message.reply_text(f"{user.mention_html()} a primit mute pentru {minutes} minute. Motiv: {motive}", parse_mode="HTML")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("Folosește comanda ca reply la mesaj.")

    if not await is_admin(update):
        return

    user = update.message.reply_to_message.from_user
    motive = " ".join(context.args) or "Fără motiv"
    await update.effective_chat.ban_member(user.id)
    await update.message.reply_text(f"{user.mention_html()} a fost banat. Motiv: {motive}", parse_mode="HTML")

async def is_admin(update: Update) -> bool:
    member = await update.effective_chat.get_member(update.effective_user.id)
    return member.status in ("administrator", "creator")

# ====== MAIN APP ======

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reguli", reguli))
    application.add_handler(CommandHandler("warn", warn))
    application.add_handler(CommandHandler("mute", mute))
    application.add_handler(CommandHandler("ban", ban))

    application.run_polling()

if __name__ == "__main__":
    main()
