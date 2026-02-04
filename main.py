from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================
BOT_TOKEN = "8574662523:AAGSg0u6Uq_y0G2OP8jWj-DYxC9AYwwRq80"
ADMIN_ID = 7112312810  # your admin id
# ==========================================

pending_users = set()
approved_users = set()

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id in approved_users:
        await update.message.reply_text(
            "🎉 *Welcome Back!*\n\n"
            "✅ You are already approved.\n"
            "📤 Please send your *Referral Text* now.",
            parse_mode="Markdown"
        )
        return

    if user.id in pending_users:
        await update.message.reply_text(
            "⏳ *Approval Pending*\n\n"
            "🛑 Please wait for admin approval.",
            parse_mode="Markdown"
        )
        return

    pending_users.add(user.id)

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
        ]
    ]

    text = (
        "📩 *Approval Request*\n\n"
        f"👤 *Name:* {user.first_name}\n"
        f"🆔 *User ID:* `{user.id}`\n"
        f"🔗 *Username:* @{user.username if user.username else 'Not Set'}"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

    await update.message.reply_text(
        "✅ *Approval request sent to admin.*\n"
        "⏳ Please wait…",
        parse_mode="Markdown"
    )


# ---------- APPROVE / REJECT ----------
async def approval_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = int(data.split("_")[1])

    if data.startswith("approve"):
        approved_users.add(user_id)
        pending_users.discard(user_id)

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🎉 *You Are Approved!*\n\n"
                "📤 Now send your *Referral Text*."
            ),
            parse_mode="Markdown"
        )

        await query.edit_message_text(
            "✅ *User Approved Successfully!*",
            parse_mode="Markdown"
        )

    elif data.startswith("reject"):
        pending_users.discard(user_id)

        await context.bot.send_message(
            chat_id=user_id,
            text="❌ *Your request was rejected by admin.*",
            parse_mode="Markdown"
        )

        await query.edit_message_text(
            "❌ *User Rejected!*",
            parse_mode="Markdown"
        )


# ---------- REFERRAL TEXT ----------
async def referral_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in approved_users:
        await update.message.reply_text(
            "🚫 *Access Denied*\n\n"
            "❗ You are not approved yet.",
            parse_mode="Markdown"
        )
        return

    text = update.message.text

    # Extract only numeric IDs
    ids = [i for i in text.split() if i.isdigit()]
    
    # Count total IDs
    total_ids = len(ids)
    
    # Join IDs with newlines for easy copying
    clean_ids = "\n".join(ids)

    # Send formatted message to admin
    formatted_text = (
        "🚀 *NEW REFERRALS RECEIVED*\n\n"
        f"👤 *User:* {user.first_name}\n"
        f"🆔 *User ID:* `{user.id}`\n"
        f"📊 *Total IDs:* {total_ids}\n"
        f"💰 *Total Amount:* ₹{total_ids * 3}\n\n"
        "📋 *IDs (tap to copy):*"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=formatted_text,
        parse_mode="Markdown"
    )
    
    # Send IDs separately in monospace format for easy copying
    if clean_ids:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"```\n{clean_ids}\n```",
            parse_mode="Markdown"
        )
    else:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text="❌ No valid IDs found in the message."
        )

    # Confirm to user
    await update.message.reply_text(
        f"✅ *Referral text sent successfully!*\n\n"
        f"📊 Total IDs extracted: {total_ids}",
        parse_mode="Markdown"
    )


# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(approval_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, referral_text))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
