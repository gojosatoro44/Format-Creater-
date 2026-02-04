import os
import re
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ===== VARIABLES =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

approved_users = set()
pending_users = {}
user_states = {}

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id in approved_users:
        await show_options(update, context)
        return

    keyboard = [[InlineKeyboardButton("📨 Send Approval", callback_data="send_approval")]]
    await update.message.reply_text(
        "🔒 Approval required to use this bot.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== SEND APPROVAL =====
async def approval_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    pending_users[user.id] = user

    keyboard = [[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
    ]]

    msg = (
        f"📩 *Approval Request*\n\n"
        f"👤 Name: {user.full_name}\n"
        f"🆔 User ID: `{user.id}`\n"
        f"🔗 Username: @{user.username if user.username else 'N/A'}"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=msg,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await query.edit_message_text("✅ Approval request sent to admin.")

# ===== ADMIN APPROVE / REJECT =====
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, uid = query.data.split("_")
    uid = int(uid)

    if action == "approve":
        approved_users.add(uid)
        await context.bot.send_message(
            chat_id=uid,
            text="✅ You are approved!\n\nChoose an option:"
        )
        await show_options_to_user(uid, context)
        await query.edit_message_text("✅ User Approved")
    else:
        await context.bot.send_message(
            chat_id=uid,
            text="❌ You aren’t allowed to use this bot.\nAny queries? DM @dtxzahid"
        )
        await query.edit_message_text("❌ User Rejected")

# ===== OPTIONS =====
async def show_options(update, context):
    keyboard = [
        [InlineKeyboardButton("1️⃣ Single Amount", callback_data="single")],
        [InlineKeyboardButton("2️⃣ Different Amount", callback_data="different")]
    ]
    await update.message.reply_text(
        "Choose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_options_to_user(uid, context):
    keyboard = [
        [InlineKeyboardButton("1️⃣ Single Amount", callback_data="single")],
        [InlineKeyboardButton("2️⃣ Different Amount", callback_data="different")]
    ]
    await context.bot.send_message(
        chat_id=uid,
        text="Choose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== OPTION HANDLER (FIXED) =====
async def option_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_states[query.from_user.id] = {
        "mode": query.data,           # single / different
        "step": "waiting_referrals",  # FIXED STEP SYSTEM
        "ids": []
    }

    await query.edit_message_text("📥 Send the referral text now.")

# ===== TEXT HANDLER (FIXED LOOP ISSUE) =====
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_states:
        return

    state = user_states[user_id]

    # STEP 1: GET REFERRALS
    if state["step"] == "waiting_referrals":
        ids = re.findall(r"\b\d{8,12}\b", text)

        if not ids:
            await update.message.reply_text("❌ No valid User IDs found. Send referral text again.")
            return

        state["ids"] = ids
        state["step"] = "waiting_amount"

        await update.message.reply_text("💰 Enter amount to add:")
        return

    # STEP 2: GET AMOUNT
    if state["step"] == "waiting_amount":
        amount = text
        ids = state["ids"]

        if state["mode"] == "single":
            output = f"[{','.join(ids)} {amount}]"
        else:
            output = "[\n" + "\n".join(f"{i} {amount}" for i in ids) + "\n]"

        await update.message.reply_text(f"✅ Done:\n\n{output}")

        # IMPORTANT: CLEAR STATE (FIX)
        del user_states[user_id]

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(approval_request, pattern="send_approval"))
    app.add_handler(CallbackQueryHandler(admin_action, pattern="approve_|reject_"))
    app.add_handler(CallbackQueryHandler(option_handler, pattern="single|different"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
