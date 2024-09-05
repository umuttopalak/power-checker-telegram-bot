import logging
import os

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          ConversationHandler, MessageHandler, filters)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi! Use /chatid to get your chat ID.')


async def chatid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the user's chat ID."""
    chat_id = update.message.chat_id
    await update.message.reply_text(f'Your chat ID is: {chat_id}')


def main() -> None:
    """Start the bot."""
    TOKEN = os.environ.get("TOKEN")
    application = Application.builder().token(token=TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("chatid", chatid))

    application.run_polling()

if __name__ == '__main__':
    load_dotenv()
    main()
