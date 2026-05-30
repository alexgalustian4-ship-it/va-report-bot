import os
import logging
from datetime import datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters,
    CallbackQueryHandler
)
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
REPORT_CHAT_ID = os.environ.get("REPORT_CHAT_ID")
TIMEZONE = pytz.timezone("Asia/Bangkok")

va_registry = {}

(
    NAME, ACCOUNT, VIEWS, FOLLOWERS,
    SCREENSHOT_ACTIVITY, SCREENSHOT_PROFILE, PROBLEMS, PROBLEM_TEXT
) = range(8)


async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, data in va_registry.items():
        reported = data.get("reported_today", [])
        name = data.get("name", "VA")
        if not reported:
            msg = f"⏰ *Reminder, {name}!*\n\nYou haven't submitted your daily report yet!\nTap /start now 👇"
        elif len(reported) == 1:
            msg = f"⏰ *Reminder, {name}!*\n\nYou only submitted 1 report today ({reported[0]['account']}).\nManage a second account? Tap /start!"
        else:
            continue
        try:
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Could not send reminder to {chat_id}: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    chat_id = update.effective_chat.id
    context.user_data['chat_id'] = chat_id

    if chat_id not in va_registry:
        va_registry[chat_id] = {"name": None, "reported_today": []}

    reported = va_registry[chat_id].get("reported_today", [])
    if len(reported) >= 2:
        await update.message.reply_text("✅ You already submitted reports for both accounts today!\nSee you tomorrow 🙌")
        return ConversationHandler.END

    # Known VA — skip name step
    if va_registry[chat_id].get("name"):
        context.user_data['name'] = va_registry[chat_id]["name"]
        context.user_data['date'] = datetime.now(TIMEZONE).strftime("%d/%m/%Y")
        if reported:
            await update.message.reply_text(
                f"📋 *DAILY REPORT — Account 2*\n\n"
                f"Hey {context.user_data['name']}! You already reported for *{reported[0]['account']}*.\n"
                f"👤 What's your second account?\n_(ex: @elena)_",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"📋 *DAILY REPORT*\n\n"
                f"Hey {context.user_data['name']}! 👋\n"
                f"👤 Which Instagram account did you manage today?\n_(ex: @elena)_",
                parse_mode="Markdown"
            )
        return ACCOUNT

    # New VA — show welcome with button
    keyboard = [[InlineKeyboardButton("📋 Start my report", callback_data="begin_report")]]
    await update.message.reply_text(
        "👋 *Welcome to Reports VA!*\n\n"
        "Every day after your session, submit your daily report here.\n"
        "It takes less than 2 minutes ✅\n\n"
        "Tap the button to get started 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return NAME


async def begin_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✏️ What's your *first and last name*?",
        parse_mode="Markdown"
    )


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data['name'] = name
    context.user_data['date'] = datetime.now(TIMEZONE).strftime("%d/%m/%Y")
    chat_id = context.user_data['chat_id']
    va_registry[chat_id]["name"] = name

    await update.message.reply_text(
        f"👤 Which Instagram account did you manage today?\n_(ex: @elena)_",
        parse_mode="Markdown"
    )
    return ACCOUNT


async def get_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = update.message.text.strip()
    chat_id = context.user_data['chat_id']
    reported = va_registry[chat_id].get("reported_today", [])

    if any(r['account'] == account for r in reported):
        await update.message.reply_text(
            f"⚠️ You already submitted a report for *{account}* today!\nPlease enter a different account.",
            parse_mode="Markdown"
        )
        return ACCOUNT

    context.user_data['account'] = account
    await update.message.reply_text("👁️ How many *views* on the posts today?", parse_mode="Markdown")
    return VIEWS


async def get_views(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("⚠️ Please enter a *number* only. (ex: 400)", parse_mode="Markdown")
        return VIEWS
    context.user_data['views'] = text
    await update.message.reply_text("📈 How many *new followers* today?", parse_mode="Markdown")
    return FOLLOWERS


async def get_followers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("⚠️ Please enter a *number* only. (ex: 50)", parse_mode="Markdown")
        return FOLLOWERS
    context.user_data['followers'] = text
    await update.message.reply_text(
        "📊 Send the *Time Management screenshot*\n\n"
        "👉 Settings → Your Activity → *Time Management*\n"
        "📸 Screenshot the time spent today",
        parse_mode="Markdown"
    )
    return SCREENSHOT_ACTIVITY


async def get_screenshot_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['photo_activity'] = update.message.photo[-1].file_id
        await update.message.reply_text("🖼️ Now send the *profile screenshot* of the account", parse_mode="Markdown")
        return SCREENSHOT_PROFILE
    else:
        await update.message.reply_text("⚠️ Please send a *photo*, not text.", parse_mode="Markdown")
        return SCREENSHOT_ACTIVITY


async def get_screenshot_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['photo_profile'] = update.message.photo[-1].file_id
        keyboard = [
            [InlineKeyboardButton("✅ No issues", callback_data="no_problem")],
            [InlineKeyboardButton("⚠️ Yes, I have an issue", callback_data="yes_problem")]
        ]
        await update.message.reply_text("🚨 Any *issues* today?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return PROBLEMS
    else:
        await update.message.reply_text("⚠️ Please send a *photo*, not text.", parse_mode="Markdown")
        return SCREENSHOT_PROFILE


async def get_problems(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "no_problem":
        context.user_data['problems'] = "None"
        await query.edit_message_text("✅ Perfect, no issues!")
        await send_report(update, context)
        return ConversationHandler.END
    elif query.data == "yes_problem":
        await query.edit_message_text("✍️ Describe the issue:")
        return PROBLEM_TEXT


async def get_problem_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['problems'] = update.message.text
    await send_report(update, context)
    return ConversationHandler.END


async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data
    chat_id = d['chat_id']
    now_str = datetime.now(TIMEZONE).strftime('%H:%M')

    entry = {
        "account": d['account'],
        "views": d['views'],
        "followers": d['followers'],
        "problems": d['problems'],
        "time": now_str
    }
    va_registry[chat_id]["reported_today"].append(entry)
    reported_count = len(va_registry[chat_id]["reported_today"])

    report = (
        f"📋 *REPORT — {d['name']}*\n"
        f"📅 {d['date']} • {now_str}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 Account: {d['account']}\n"
        f"👁️ Views: {d['views']}\n"
        f"📈 New followers: {d['followers']}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🚨 Issues: {d['problems']}"
    )

    await context.bot.send_message(chat_id=int(REPORT_CHAT_ID), text=report, parse_mode="Markdown")

    for key in ['photo_activity', 'photo_profile']:
        if key in d:
            await context.bot.send_photo(chat_id=int(REPORT_CHAT_ID), photo=d[key])

    effective_message = update.callback_query.message if update.callback_query else update.message

    if reported_count < 2:
        await effective_message.reply_text(
            f"🎉 *Report sent!* Thank you {d['name']} 🙌\n\nDo you manage a second account? Type /start!",
            parse_mode="Markdown"
        )
    else:
        await effective_message.reply_text(
            f"🎉 *All reports submitted!* Thank you {d['name']} 🙌\nSee you tomorrow!",
            parse_mode="Markdown"
        )


async def my_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    data = va_registry.get(chat_id)

    if not data or not data.get("reported_today"):
        await update.message.reply_text("📭 You haven't submitted any report today yet.\nType /start to submit one!")
        return

    today = datetime.now(TIMEZONE).strftime("%d/%m/%Y")
    lines = [f"📋 *Your reports — {today}*\n━━━━━━━━━━━━━━━"]
    for i, r in enumerate(data["reported_today"], 1):
        lines.append(
            f"\n*Account {i}: {r['account']}*\n"
            f"👁️ Views: {r['views']}\n"
            f"📈 Followers: {r['followers']}\n"
            f"🚨 Issues: {r['problems']}\n"
            f"🕐 Sent at: {r['time']}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(TIMEZONE).strftime("%d/%m/%Y")
    if not va_registry:
        await update.message.reply_text("📊 No VAs have reported yet today.")
        return

    lines = [f"📊 *STATS — {today}*\n━━━━━━━━━━━━━━━"]
    for chat_id, data in va_registry.items():
        reported = data.get("reported_today", [])
        name = data.get("name") or "Unknown"
        if reported:
            accounts = ", ".join(r['account'] for r in reported)
            lines.append(f"✅ {name} — {accounts} ({len(reported)}/2)")
        else:
            lines.append(f"❌ {name} — No report yet")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Report cancelled. Type /start to restart.")
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    job_queue = app.job_queue
    reminder_time = time(hour=23, minute=0, tzinfo=TIMEZONE)
    job_queue.run_daily(send_reminder, time=reminder_time)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("report", start)],
        states={
            NAME: [
                CallbackQueryHandler(begin_report, pattern="^begin_report$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)
            ],
            ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_account)],
            VIEWS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_views)],
            FOLLOWERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_followers)],
            SCREENSHOT_ACTIVITY: [
                MessageHandler(filters.PHOTO, get_screenshot_activity),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_screenshot_activity)
            ],
            SCREENSHOT_PROFILE: [
                MessageHandler(filters.PHOTO, get_screenshot_profile),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_screenshot_profile)
            ],
            PROBLEMS: [CallbackQueryHandler(get_problems)],
            PROBLEM_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_problem_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("myreports", my_reports))

    logger.info("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
