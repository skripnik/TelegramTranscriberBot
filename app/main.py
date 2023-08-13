import logging
import os
from telegram.ext import ApplicationBuilder
from TelegramService import TelegramService
from dotenv import load_dotenv

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    load_dotenv()

    TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
    application = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

    telegram_service = TelegramService(application)
    telegram_service.setup()

    application.run_polling()
