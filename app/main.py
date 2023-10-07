import logging
import os
from dotenv import load_dotenv
from app.TelegramService import TelegramService

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.ERROR,
    )

    load_dotenv()
    telegram_api_token: str = os.getenv("TELEGRAM_API_TOKEN")
    telegram_service = TelegramService(
        telegram_api_token=telegram_api_token, local_mode=True
    )
    telegram_service.setup_handlers()
