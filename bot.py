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
        "📊 *DAILY REPORT — AMA*\n\n"
        "👤 Quel compte Instagram as-tu géré aujourd'hui ?\n_(ex: @nom\\_du\\_compte)_",
        parse_mode="Markdown"
    )
    return ACCOUNT

async def get_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['account'] = update.message.text
    await update.message.reply_text("⏰ Heure de *début* de session ? _(ex: 14:00)_", parse_mode="Markdown")
    return START_TIME

async def get_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['start_time'] = update.message.text
    await update.message.reply_text("⏰ Heure de *fin* ? _(ex: 16:30)_", parse_mode="Markdown")
    return END_TIME

async def get_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['end_time'] = update.message.text
    await update.message.reply_text("🔄 Combien de fois tu t'es *connecté* au compte aujourd'hui ?", parse_mode="Markdown")
    return CONNECTIONS

async def get_connections(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['connections'] = update.message.text
    await update.message.reply_text("➕ Combien de *follows* as-tu fait ?", parse_mode="Markdown")
    return FOLLOWS

async def get_follows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['follows'] = update.message.text
    await update.message.reply_text("👁️ Combien de *stories* as-tu vues ?", parse_mode="Markdown")
    return STORIES

async def get_stories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['stories'] = update.message.text
    await update.message.reply_text("❤️ Combien de *posts* as-tu likés ?", parse_mode="Markdown")
    return LIKES

async def get_likes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['likes'] = update.message.text
    await update.message.reply_text("💬 Combien de *commentaires* as-tu laissés ?", parse_mode="Markdown")
    return COMMENTS

async def get_comments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['comments'] = update.message.text
    await update.message.reply_text(
        "📸 Envoie le *screenshot de ton activité Instagram*\n_(Paramètres → Votre activité)_",
        parse_mode="Markdown"
    )
    return SCREENSHOT_ACTIVITY

async def get_screenshot_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['photo_activity'] = update.message.photo[-1].file_id
        await update.message.reply_text("📸 Maintenant le *screenshot de la page profil* du compte", parse_mode="Markdown")
        return SCREENSHOT_PROFILE
    else:
        await update.message.reply_text("⚠️ Envoie une *photo* (screenshot), pas du texte.", parse_mode="Markdown")
        return SCREENSHOT_ACTIVITY

async def get_screenshot_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['photo_profile'] = update.message.photo[-1].file_id
        await update.message.reply_text("⚠️ Des *problèmes* aujourd'hui ?\n_(Écris \"Aucun\" si tout va bien)_", parse_mode="Markdown")
        return PROBLEMS
    else:
        await update.message.reply_text("⚠️ Envoie une *photo* (screenshot), pas du texte.", parse_mode="Markdown")
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
        duration_str = f"{hours}h{minutes:02d}"
    except:
        duration_str = f"{d['start_time']} → {d['end_time']}"

    report = (
        f"📊 *REPORT — {d['va_name']}*\n"
        f"📅 {d['date']} | ⏱️ {duration_str}\n"
        f"👤 Compte : {d['account']}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔄 Connexions : {d['connections']}\n"
        f"➕ Follows
