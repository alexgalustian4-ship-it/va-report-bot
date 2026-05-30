import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters,
    CallbackQueryHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
REPORT_CHAT_ID = os.environ.get("REPORT_CHAT_ID")

(
    ACCOUNT, VIEWS, FOLLOWERS,
    SCREENSHOT_ACTIVITY, SCREENSHOT_PROFILE, PROBLEMS, PROBLEM_TEXT
) = range(7)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['va_name'] = update.effective_user.first_name
    context.user_data['date'] = datetime.now().strftime("%d/%m/%Y")

    await update.message.reply_text(
        "📋 *DAILY REPORT*\n\n"
        "👤 Quel compte Instagram as-tu géré aujourd'hui?\n"
        "_(ex: @elena)_",
        parse_mode="Markdown"
    )
    return ACCOUNT


async def get_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['account'] = update.message.text

    await update.message.reply_text(
        "👁️ Combien de *vues* sur les posts aujourd'hui?",
        parse_mode="Markdown"
    )
    return VIEWS


async def get_views(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['views'] = update.message.text

    await update.message.reply_text(
        "📈 Combien d'*abonnés gagnés* aujourd'hui?",
        parse_mode="Markdown"
    )
    return FOLLOWERS


async def get_followers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['followers'] = update.message.text

    await update.message.reply_text(
        "📊 Envoie le *screenshot de ton activité* Instagram\n"
        "_(Paramètres → Votre activité)_",
        parse_mode="Markdown"
    )
    return SCREENSHOT_ACTIVITY


async def get_screenshot_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['photo_activity'] = update.message.photo[-1].file_id
        await update.message.reply_text(
            "🖼️ Maintenant envoie le *screenshot du profil* du compte",
            parse_mode="Markdown"
        )
        return SCREENSHOT_PROFILE
    else:
        await update.message.reply_text("⚠️ Envoie une *photo*, pas du texte.", parse_mode="Markdown")
        return SCREENSHOT_ACTIVITY


async def get_screenshot_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['photo_profile'] = update.message.photo[-1].file_id

        keyboard = [
            [InlineKeyboardButton("✅ Aucun problème", callback_data="no_problem")],
            [InlineKeyboardButton("⚠️ Oui, j'ai un problème", callback_data="yes_problem")]
        ]
        await update.message.reply_text(
            "🚨 Des *problèmes* aujourd'hui?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return PROBLEMS
    else:
        await update.message.reply_text("⚠️ Envoie une *photo*, pas du texte.", parse_mode="Markdown")
        return SCREENSHOT_PROFILE


async def get_problems(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "no_problem":
        context.user_data['problems'] = "Aucun"
        await query.edit_message_text("✅ Parfait, aucun problème!")
        await send_report(update, context)
        return ConversationHandler.END
    else:
        await query.edit_message_text("✍️ Décris le problème :")
        return PROBLEM_TEXT


async def get_problem_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['problems'] = update.message.text
    await send_report(update, context)
    return ConversationHandler.END


async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data

    report = (
        f"📋 *REPORT — {d['va_name']}*\n"
        f"📅 {d['date']} • {datetime.now().strftime('%H:%M')}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 Compte : {d['account']}\n"
        f"👁️ Vues : {d['views']}\n"
        f"📈 Abonnés gagnés : {d['followers']}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🚨 Problèmes : {d['problems']}"
    )

    await context.bot.send_message(
        chat_id=int(REPORT_CHAT_ID),
        text=report,
        parse_mode="Markdown"
    )

    for key in ['photo_activity', 'photo_profile']:
        if key in d:
            await context.bot.send_photo(
                chat_id=int(REPORT_CHAT_ID),
                photo=d[key]
            )

    # Confirm to VA
    effective_message = update.callback_query.message if update.callback_query else update.message
    await effective_message.reply_text(
        f"🎉 *Report envoyé!* Merci {d['va_name']} 🙌",
        parse_mode="Markdown"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Report annulé. Tape /start pour recommencer.")
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("report", start)],
        states={
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
    logger.info("Bot démarré...")
    app.run_polling()


if __name__ == "__main__":
    main()
