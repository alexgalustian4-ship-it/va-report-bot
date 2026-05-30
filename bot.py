import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
REPORT_CHAT_ID = os.environ.get("REPORT_CHAT_ID")
REPORT_THREAD_ID = os.environ.get("REPORT_THREAD_ID")

(
    ACCOUNT, START_TIME, END_TIME, CONNECTIONS,
    FOLLOWS, STORIES, LIKES, COMMENTS,
    SCREENSHOT_ACTIVITY, SCREENSHOT_PROFILE, PROBLEMS
) = range(11)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['va_name'] = update.effective_user.first_name
    context.user_data['date'] = datetime.now().strftime("%d/%m/%Y")
    await update.message.reply_text(
        "DAILY REPORT - AMA\n\nQuel compte Instagram as-tu gere aujourd'hui? (ex: @nom_du_compte)"
    )
    return ACCOUNT

async def get_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['account'] = update.message.text
    await update.message.reply_text("Heure de debut de session? (ex: 14:00)")
    return START_TIME

async def get_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['start_time'] = update.message.text
    await update.message.reply_text("Heure de fin? (ex: 16:30)")
    return END_TIME

async def get_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['end_time'] = update.message.text
    await update.message.reply_text("Combien de fois tu t'es connecte au compte aujourd'hui?")
    return CONNECTIONS

async def get_connections(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['connections'] = update.message.text
    await update.message.reply_text("Combien de follows as-tu fait?")
    return FOLLOWS

async def get_follows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['follows'] = update.message.text
    await update.message.reply_text("Combien de stories as-tu vues?")
    return STORIES

async def get_stories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['stories'] = update.message.text
    await update.message.reply_text("Combien de posts as-tu likes?")
    return LIKES

async def get_likes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['likes'] = update.message.text
    await update.message.reply_text("Combien de commentaires as-tu laisses?")
    return COMMENTS

async def get_comments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['comments'] = update.message.text
    await update.message.reply_text(
        "Envoie le screenshot de ton activite Instagram (Parametres -> Votre activite)"
    )
    return SCREENSHOT_ACTIVITY

async def get_screenshot_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['photo_activity'] = update.message.photo[-1].file_id
        await update.message.reply_text("Maintenant envoie le screenshot de la page profil du compte")
        return SCREENSHOT_PROFILE
    else:
        await update.message.reply_text("Envoie une photo (screenshot), pas du texte.")
        return SCREENSHOT_ACTIVITY

async def get_screenshot_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['photo_profile'] = update.message.photo[-1].file_id
        await update.message.reply_text("Des problemes aujourd'hui? (Ecris 'Aucun' si tout va bien)")
        return PROBLEMS
    else:
        await update.message.reply_text("Envoie une photo (screenshot), pas du texte.")
        return SCREENSHOT_PROFILE

async def get_problems(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['problems'] = update.message.text
    d = context.user_data
    try:
        fmt = "%H:%M"
        start = datetime.strptime(d['start_time'], fmt)
        end = datetime.strptime(d['end_time'], fmt)
        duration = end - start
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        duration_str = str(hours) + "h" + str(minutes).zfill(2)
    except Exception:
        duration_str = d['start_time'] + " -> " + d['end_time']

    report = (
        "REPORT - " + d['va_name'] + "\n"
        "Date: " + d['date'] + " | Duree: " + duration_str + "\n"
        "Compte: " + d['account'] + "\n"
        "---------------\n"
        "Connexions: " + d['connections'] + "\n"
        "Follows: " + d['follows'] + "\n"
        "Stories vues: " + d['stories'] + "\n"
        "Posts likes: " + d['likes'] + "\n"
        "Commentaires: " + d['comments'] + "\n"
        "---------------\n"
        "Problemes: " + d['problems'] + "\n"
        "Envoye a: " + datetime.now().strftime('%H:%M')
    )

    kwargs = {"chat_id": int(REPORT_CHAT_ID), "text": report}
    if REPORT_THREAD_ID:
        kwargs["message_thread_id"] = int(REPORT_THREAD_ID)
    await context.bot.send_message(**kwargs)

    for key in ['photo_activity', 'photo_profile']:
        if key in d:
            photo_kwargs = {"chat_id": int(REPORT_CHAT_ID), "photo": d[key]}
            if REPORT_THREAD_ID:
                photo_kwargs["message_thread_id"] = int(REPORT_THREAD_ID)
            await context.bot.send_photo(**photo_kwargs)

    await update.message.reply_text(
        "Report enregistre! Duree: " + duration_str + " - Merci " + d['va_name']
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Report annule. Tape /report pour recommencer.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("report", start), CommandHandler("start", start)],
        states={
            ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_account)],
            START_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_start_time)],
            END_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_end_time)],
            CONNECTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_connections)],
            FOLLOWS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_follows)],
            STORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_stories)],
            LIKES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_likes)],
            COMMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_comments)],
            SCREENSHOT_ACTIVITY: [MessageHandler(filters.PHOTO, get_screenshot_activity),
                                   MessageHandler(filters.TEXT & ~filters.COMMAND, get_screenshot_activity)],
            SCREENSHOT_PROFILE: [MessageHandler(filters.PHOTO, get_screenshot_profile),
                                  MessageHandler(filters.TEXT & ~filters.COMMAND, get_screenshot_profile)],
            PROBLEMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_problems)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    logger.info("Bot demarre...")
    app.run_polling()

if __name__ == "__main__":
    main()
