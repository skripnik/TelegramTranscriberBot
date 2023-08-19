import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import User, Bot
from telegram.error import BadRequest, TelegramError

from app.TelegramService import TelegramService


async def check_if_logged_in(bot: Bot) -> bool:
    try:
        user = await bot.get_me()
    except BadRequest:
        return False

    return isinstance(user, User)


async def log_out_if_logged_in(bot: Bot) -> None:
    if not await check_if_logged_in(bot):
        logging.info("User is already logged out.")
        return

    logging.info("User is logged in. Attempting to log out...")

    try:
        await bot.log_out()
    except TelegramError as error:
        raise RuntimeError(f"Failed to log out. Error: {error.message}")

    if not await check_if_logged_in(bot):
        logging.info("Logged out successfully.")
    else:
        raise RuntimeError("Failed to log out.")


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
    asyncio.run(log_out_if_logged_in(telegram_service.bot))
