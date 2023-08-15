import logging
import os

from telegram.ext import ApplicationBuilder, AIORateLimiter
from TelegramService import TelegramService
from dotenv import load_dotenv
from config import TELEGRAM_BASE_URL, TELEGRAM_BASE_FILE_URL

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    load_dotenv()

    TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

    rate_limiter = AIORateLimiter(
        overall_max_rate=30,
        overall_time_period=1,
        group_max_rate=20,
        group_time_period=60,
        max_retries=3,
    )

    application_builder = ApplicationBuilder()
    application_builder.token(TELEGRAM_API_TOKEN)
    application_builder.base_url(TELEGRAM_BASE_URL)
    application_builder.base_file_url(TELEGRAM_BASE_FILE_URL)
    application_builder.local_mode(True)
    application_builder.read_timeout(60)
    application_builder.write_timeout(60)
    application_builder.connect_timeout(60)
    application_builder.pool_timeout(60)
    application_builder.rate_limiter(rate_limiter)
    application = application_builder.build()

    telegram_service = TelegramService(application)
    telegram_service.setup()

    application.run_polling()
