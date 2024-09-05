import logging
import os

import requests
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          ConversationHandler, MessageHandler, filters)

NAME, SURNAME, EMAIL, PHONE = range(4)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


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

    logger.info(f"Sending user data to backend: {context.user_data}")

    firstname = context.user_data['firstname']
    lastname = context.user_data['lastname']
    email = context.user_data['email']
    phone = context.user_data['phone']
    try:
        backend_url = os.environ.get('BACKEND_URL')
        payload = {
            'firstname': firstname,
            'lastname': lastname,
            'email': email,
            'phone': phone,
            'chat_id': chat_id
        }
        response = requests.post(backend_url, json=payload)
        logger.info("Backend response: %s", response.status_code)

        if response.status_code == 200:
            await update.message.reply_text("Bilgileriniz başarıyla kaydedildi. Kısa süre içinde sizinle iletişime geçeceğiz.")
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


def main() -> None:
    """Start the bot."""
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

    application.run_polling()


if __name__ == '__main__':
    main()
