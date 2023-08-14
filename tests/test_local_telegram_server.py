import os

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, Application

from app.config import TELEGRAM_BASE_URL, TELEGRAM_BASE_FILE_URL


def test_local_telegram_server():
    load_dotenv()
    TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

    application_builder = ApplicationBuilder()
    application_builder.token(TELEGRAM_API_TOKEN)
    application_builder.base_url(TELEGRAM_BASE_URL)
    application_builder.base_file_url(TELEGRAM_BASE_FILE_URL)
    application_builder.local_mode(True)
    application = application_builder.build()

    assert isinstance(application, Application)
