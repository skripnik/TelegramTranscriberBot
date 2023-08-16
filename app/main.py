import logging
from TelegramService import TelegramService

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    telegram_service = TelegramService()
    telegram_service.build_app(True)
    telegram_service.setup()
    telegram_service.run_polling()

