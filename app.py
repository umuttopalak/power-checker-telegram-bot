import logging
import os
import threading
import time

import requests
from dotenv import load_dotenv
from flask import Flask
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          ConversationHandler, MessageHandler, filters)

NAME, SURNAME, EMAIL, PHONE = range(4)

# Telegram bot için logging ayarları
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask uygulaması (portu dinlemek için)
app = Flask(__name__)


@app.route('/')
def index():
    return "Bot is running!"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command, requests first name."""
    await update.message.reply_text("Lütfen adınızı giriniz:")
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the user's first name."""
    context.user_data['firstname'] = update.message.text
    await update.message.reply_text("Lütfen soyadınızı giriniz:")
    return SURNAME


async def get_surname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the user's last name."""
    context.user_data['lastname'] = update.message.text
    await update.message.reply_text("Lütfen e-posta adresinizi giriniz:")
    return EMAIL


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the user's email and stores it."""
    context.user_data['email'] = update.message.text
    await update.message.reply_text("Lütfen telefon numaranızı giriniz:")
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the user's phone number and stores it."""
    context.user_data['phone'] = update.message.text
    chat_id = update.message.chat_id
    context.user_data['chat_id'] = chat_id

    firstname = context.user_data['firstname']
    lastname = context.user_data['lastname']
    email = context.user_data['email']
    phone = context.user_data['phone']

    try:
        backend_url = os.environ.get('BACKEND_URL')
        payload = {
            'first_name': firstname,
            'last_name': lastname,
            'email': email,
            'phone_number': phone,
            'chat_id': str(chat_id),
            'has_license': False
        }
        response = requests.post(backend_url, json=payload)
        logger.info("url: %s, payload: %s, response: %s",
                    backend_url, payload, response)

        if response.status_code == 201:
            await update.message.reply_text("Bilgileriniz başarıyla kaydedildi. Kısa süre içinde sizinle iletişime geçeceğiz.")
        elif response.status_code == 400:
            await update.message.reply_text("Eksik bilgileriniz bulunmaktadır, lütfen tekrar başlayınız.")
        elif response.status_code == 409:
            await update.message.reply_text("Kullanıcını kaydınız bulunmaktadır, lütfen bizimle iletişime geçiniz (admin@umuttopalak.com).")
        else:
            logger.error("Backend returned an error: %s", response)
            await update.message.reply_text("Bir hata oluştu. Lütfen daha sonra tekrar deneyiniz.")
    except Exception as e:
        logger.error(f"Error sending data to backend: {e}")
        await update.message.reply_text("Bağlantı hatası, lütfen daha sonra tekrar deneyiniz.")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation."""
    await update.message.reply_text("İşlem iptal edildi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def run_flask():
    """Flask sunucusunu başlatır."""
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


def periodic_task():
    """Her 1 dakikada bir çalışan görev."""
    while True:
        try:
            url = os.environ.get("PERIODIC_TASK_URL")
            admin_key = os.environ.get("ADMIN_KEY")
            header = {"admin-key" : admin_key}
            response = requests.get(url, headers=header)
            logger.info(f"Periodic task sent a request to {url}. Response: {response.status_code}")
        except Exception as e:
            logger.error(f"Error in periodic task: {e}")
        time.sleep(2700)


def main():
    """Telegram botunu başlatır."""
    load_dotenv()
    TOKEN = os.environ.get("TOKEN")

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
    logger.info("Bot is running...")

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    periodic_task_thread = threading.Thread(target=periodic_task)
    periodic_task_thread.start()

    application.run_polling()


if __name__ == '__main__':
    main()
