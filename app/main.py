import logging
import os
from telegram.ext import ApplicationBuilder
from TelegramService import TelegramService
from dotenv import load_dotenv

from app.config import TELEGRAM_BASE_URL, TELEGRAM_BASE_FILE_URL

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    load_dotenv()

    TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

    application_builder = ApplicationBuilder()
    application_builder.token(TELEGRAM_API_TOKEN)
    application_builder.base_url(TELEGRAM_BASE_URL)
    application_builder.base_file_url(TELEGRAM_BASE_FILE_URL)
    application_builder.local_mode(True)
    application = application_builder.build()

    telegram_service = TelegramService(application)
    telegram_service.setup()

    application.run_polling()
