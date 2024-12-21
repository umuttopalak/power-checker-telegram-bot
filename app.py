import logging
import os
import re
import threading
import time

import requests
from dotenv import load_dotenv
from flask import Flask
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          ConversationHandler, MessageHandler, filters)

NAME, SURNAME, EMAIL, PHONE = range(4)

# Logging configuration for Telegram bot
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask application (for port listening)
app = Flask(__name__)


def validate_email(email):
    """Validate email format."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    """Validate phone number format."""
    pattern = r'^\+?[0-9]{10,15}$'
    return re.match(pattern, phone) is not None


@app.route('/')
def index():
    return "Bot is running!"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command, requests first name. Resets any ongoing conversation."""
    # Clear any existing user data
    context.user_data.clear()

    await update.message.reply_text(
        "Welcome! Let's start your registration process.\n"
        "You can use /cancel at any time to stop the process.\n\n"
        "Please enter your first name:"
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the user's first name."""
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("Name is too short. Please enter a valid name:")
        return NAME

    context.user_data['firstname'] = name
    await update.message.reply_text("Please enter your last name:")
    return SURNAME


async def get_surname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the user's last name."""
    surname = update.message.text.strip()
    if len(surname) < 2:
        await update.message.reply_text("Last name is too short. Please enter a valid last name:")
        return SURNAME

    context.user_data['lastname'] = surname
    await update.message.reply_text("Please enter your email address:")
    return EMAIL


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the user's email and validates it."""
    email = update.message.text.strip()
    if not validate_email(email):
        await update.message.reply_text("Invalid email format. Please enter a valid email address:")
        return EMAIL

    context.user_data['email'] = email
    await update.message.reply_text("Please enter your phone number:")
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the user's phone number, validates it and sends data to backend."""
    phone = update.message.text.strip()
    if not validate_phone(phone):
        await update.message.reply_text("Invalid phone number format. Please enter a valid phone number:")
        return PHONE

    context.user_data['phone'] = phone
    chat_id = update.message.chat_id
    context.user_data['chat_id'] = chat_id

    try:
        backend_url = os.environ.get('BACKEND_URL')
        if not backend_url:
            logger.error("BACKEND_URL environment variable is not set")
            raise ValueError("Backend URL configuration is missing")

        payload = {
            'first_name': context.user_data['firstname'],
            'last_name': context.user_data['lastname'],
            'email': context.user_data['email'],
            'phone_number': phone,
            'chat_id': str(chat_id),
            'has_license': False
        }

        response = requests.post(backend_url, json=payload, timeout=10)
        logger.info("Backend request - URL: %s, Payload: %s, Response Status: %s",
                    backend_url, payload, response.status_code)

        if response.status_code == 201:
            await update.message.reply_text("Your information has been successfully saved. We will contact you shortly.")
        elif response.status_code == 400:
            await update.message.reply_text("Missing information, please start over.")
        elif response.status_code == 409:
            await update.message.reply_text("User already exists, please contact us at admin@umuttopalak.com.")
        else:
            logger.error("Backend error - Status: %s, Response: %s",
                         response.status_code, response.text)
            await update.message.reply_text("An error occurred. Please try again later.")
    except requests.Timeout:
        logger.error("Backend request timed out")
        await update.message.reply_text("Server is not responding. Please try again later.")
    except requests.RequestException as e:
        logger.error("Network error while connecting to backend: %s", str(e))
        await update.message.reply_text("Connection error, please try again later.")
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        await update.message.reply_text("An unexpected error occurred. Please try again later.")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation."""
    await update.message.reply_text("Operation cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def run_flask():
    """Starts the Flask server."""
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


def periodic_task():
    """Task that runs every 45 minutes."""
    while True:
        try:
            url = os.environ.get("PERIODIC_TASK_URL")
            admin_key = os.environ.get("ADMIN_KEY")

            if not url or not admin_key:
                logger.error("Missing configuration for periodic task")
                time.sleep(2700)
                continue

            header = {"admin-key": admin_key}
            response = requests.get(url, headers=header, timeout=10)
            logger.info("Periodic task - URL: %s, Status: %s",
                        url, response.status_code)

            if response.status_code != 200:
                logger.warning(
                    "Periodic task failed with status code: %s", response.status_code)

        except requests.Timeout:
            logger.error("Periodic task request timed out")
        except requests.RequestException as e:
            logger.error("Network error in periodic task: %s", str(e))
        except Exception as e:
            logger.error("Unexpected error in periodic task: %s", str(e))

        time.sleep(2700)  # 45 minutes


def main():
    """Starts the Telegram bot."""
    load_dotenv()
    TOKEN = os.environ.get("TOKEN")

    if not TOKEN:
        logger.error("Telegram TOKEN is not set in environment variables")
        return

    application = Application.builder().token(token=TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_surname)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    logger.info("Bot started successfully")

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    periodic_task_thread = threading.Thread(target=periodic_task, daemon=True)
    periodic_task_thread.start()

    application.run_polling()


if __name__ == '__main__':
    main()
