"""
Telegram Bot Webhook/Polling Handler
Supports deep-link: t.me/YourBot?start=ROLL_NUMBER
"""
import logging
import asyncio
from fastapi import APIRouter, Request, Response
from telegram import Update, Bot
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters,
)
from backend.config import settings
from backend.models import SessionLocal, Student, StudentStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/bot", tags=["Bot Webhook"])

WAITING_ROLL = 1
_bot_app: Application = None


# ─── Handlers ────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args  # deep-link payload after /start

    db = SessionLocal()
    try:
        # Check if already linked
        linked = db.query(Student).filter(Student.telegram_chat_id == user.id).first()
        if linked and linked.status == StudentStatus.REGISTERED:
            await update.message.reply_text(
                f"✅ *{linked.name}*, you're already registered!\n\nUse /status to view your details.",
                parse_mode="Markdown",
            )
            return ConversationHandler.END

        # Deep-link with roll number
        if args:
            roll = args[0].upper()
            student = db.query(Student).filter(Student.roll_number == roll).first()
            if student:
                student.telegram_chat_id = user.id
                student.status = StudentStatus.REGISTERED
                db.commit()
                drive_info = f"\n📋 Drive: *{student.drive.company_name}*" if student.drive else ""
                await update.message.reply_text(
                    f"🎉 *Welcome, {student.name}!*\n\n"
                    f"You are now linked to placement updates.{drive_info}\n\n"
                    f"Use /status anytime to check your registration.",
                    parse_mode="Markdown",
                )
                return ConversationHandler.END
    finally:
        db.close()

    await update.message.reply_text(
        f"👋 Hello *{user.first_name}*! Welcome to the Placement Bot.\n\n"
        f"Please enter your *Roll Number* to link your account:",
        parse_mode="Markdown",
    )
    return WAITING_ROLL


async def receive_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    roll = update.message.text.strip().upper()
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.roll_number == roll).first()
        if not student:
            await update.message.reply_text(
                f"❌ Roll number *{roll}* not found.\n\nPlease check and try again, or contact your coordinator.",
                parse_mode="Markdown",
            )
            return WAITING_ROLL

        student.telegram_chat_id = user.id
        student.status = StudentStatus.REGISTERED
        db.commit()

        drive_info = f"\n📋 Drive: *{student.drive.company_name}*" if student.drive else ""
        await update.message.reply_text(
            f"✅ *Linked Successfully!*\n\n"
            f"Name: *{student.name}*\n"
            f"Roll: `{student.roll_number}`{drive_info}\n\n"
            f"You are now linked to placement updates. Use /status to check your status.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END
    finally:
        db.close()


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.telegram_chat_id == user.id).first()
        if not student:
            await update.message.reply_text(
                "❌ Your account is not linked yet. Use /start to link your roll number."
            )
            return

        icon = {"REGISTERED": "✅", "PENDING": "⏳", "BLOCKED": "🚫"}.get(student.status, "❓")
        drive_section = ""
        if student.drive:
            dl = student.drive.deadline.strftime("%d %b %Y, %I:%M %p")
            drive_section = f"\n\n📋 *Drive:* {student.drive.company_name}\n⏰ *Deadline:* {dl}"

        await update.message.reply_text(
            f"{icon} *Status: {student.status}*\n\n"
            f"👤 Name: *{student.name}*\n"
            f"🔢 Roll: `{student.roll_number}`\n"
            f"📨 Nudges received: *{student.nudge_count}*"
            f"{drive_section}",
            parse_mode="Markdown",
        )
    finally:
        db.close()


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Placement Nudge Bot — Help*\n\n"
        "/start — Link your roll number\n"
        "/status — Check registration status\n"
        "/help — Show this message\n\n"
        "If you face issues, contact your placement coordinator.",
        parse_mode="Markdown",
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. Use /start to begin again.")
    return ConversationHandler.END


# ─── App Builder ─────────────────────────────────────────────────────────────

def get_bot_app() -> Application:
    global _bot_app
    if _bot_app:
        return _bot_app

    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={WAITING_ROLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_roll)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("help", help_cmd))

    _bot_app = app
    return app


# ─── Polling entry point (run as separate process) ───────────────────────────

def run_polling():
    logger.info("🤖 Starting Telegram bot in polling mode...")
    app = get_bot_app()
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_polling()
