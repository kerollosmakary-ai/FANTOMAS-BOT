import asyncio
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
ALLOWED_USER_ID = 7356394102
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
ADMIN_KEY = os.getenv("ADMIN_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

def is_allowed(update: Update) -> bool:
    user = update.effective_user
    return user and user.id == ALLOWED_USER_ID

async def backend_get(path: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}{path}") as resp:
            return resp.status, await resp.json() if resp.status == 200 else await resp.text()

async def backend_post(path: str, json_data: dict, headers: dict = None):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BACKEND_URL}{path}", json=json_data, headers=headers or {}) as resp:
            return resp.status, await resp.json() if resp.status == 200 else await resp.text()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("Unauthorized.")
        return
    await update.message.reply_text(
        "FANTOMAS Control Bot\n\n"
        "Commands:\n"
        "/chat <message> - Talk to AI\n"
        "/status - Backend health\n"
        "/tokens - List API tokens\n"
        "/create_token <owner> - New token\n"
        "/providers - Available providers\n"
        "/help - Show help"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("Unauthorized.")
        return
    await update.message.reply_text(
        "FANTOMAS Helper Commands:\n\n"
        "/chat Hello world\n"
        "/status\n"
        "/tokens\n"
        "/create_token Jimmy\n"
        "/providers\n"
        "/help"
    )

async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("Unauthorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /chat <message>")
        return
    message = " ".join(context.args)
    # Need a valid token for chat. We use the admin token temporarily or a hardcoded test token.
    # For demo, use the token we created earlier.
    test_token = "sk_live_Ya35HkPBboOj7yqGFiLtSMfjY-aVqLxve_2YOD6qQYk"
    status, data = await backend_post(
        "/chat",
        {"message": message, "provider": "groq"},
        {"Authorization": f"Bearer {test_token}", "Content-Type": "application/json"}
    )
    if status == 200:
        await update.message.reply_text(
            f"AI ({data.get('provider')}): {data.get('response')}\n\n"
            f"Tokens left: {data.get('tokens_remaining')}"
        )
    else:
        await update.message.reply_text(f"Error {status}: {data}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("Unauthorized.")
        return
    status, data = await backend_get("/health")
    await update.message.reply_text(f"Backend status: {status}\n{data}" if status == 200 else f"Backend down: {status}")

async def tokens_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("Unauthorized.")
        return
    if not ADMIN_KEY:
        await update.message.reply_text("ADMIN_KEY not set in env.")
        return
    status, data = await backend_post("/admin/tokens", {}, {"x-admin-key": ADMIN_KEY, "Content-Type": "application/json"})
    # Actually GET not POST
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/admin/tokens", headers={"x-admin-key": ADMIN_KEY}) as resp:
            status = resp.status
            data = await resp.json() if resp.status == 200 else await resp.text()
    if status == 200:
        lines = []
        for t in data:
            lines.append(f"ID {t['id']}: {t['owner_name']} | bal: {t['balance']} | status: {t['status']}")
        await update.message.reply_text("Tokens:\n" + "\n".join(lines) if lines else "No tokens.")
    else:
        await update.message.reply_text(f"Error {status}: {data}")

async def create_token_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("Unauthorized.")
        return
    if not ADMIN_KEY:
        await update.message.reply_text("ADMIN_KEY not set.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /create_token <owner_name>")
        return
    owner = " ".join(context.args)
    status, data = await backend_post(
        "/admin/tokens",
        {"owner_name": owner, "balance": 100},
        {"x-admin-key": ADMIN_KEY, "Content-Type": "application/json"}
    )
    if status == 200:
        await update.message.reply_text(
            f"Token created for {owner}\n"
            f"ID: {data.get('id')}\n"
            f"Token: {data.get('api_token', 'N/A')[:20]}...\n"
            f"Balance: {data.get('balance')}"
        )
    else:
        await update.message.reply_text(f"Error {status}: {data}")

async def providers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("Unauthorized.")
        return
    status, data = await backend_get("/providers")
    if status == 200:
        lines = [f"{p['name']}: {p['status']}" for p in data.get("providers", [])]
        await update.message.reply_text("Providers:\n" + "\n".join(lines))
    else:
        await update.message.reply_text(f"Error {status}: {data}")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    await update.message.reply_text("Unknown command. Use /help")

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("chat", chat_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("tokens", tokens_command))
    application.add_handler(CommandHandler("create_token", create_token_command))
    application.add_handler(CommandHandler("providers", providers_command))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    logger.info("Bot starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
