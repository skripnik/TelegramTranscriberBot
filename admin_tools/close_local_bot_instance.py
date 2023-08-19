import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Bot

from app.TelegramService import TelegramService

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    load_dotenv()
    telegram_api_token: str = os.getenv("TELEGRAM_API_TOKEN")
    telegram_service = TelegramService(
        telegram_api_token=telegram_api_token, local_mode=True
    )
    bot: Bot = telegram_service.bot
    asyncio.run(bot.close())
