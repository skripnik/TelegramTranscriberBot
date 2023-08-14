import asyncio
import os

from dotenv import load_dotenv
from telegram import Bot, User
from telegram.error import BadRequest
from telegram.ext import ApplicationBuilder


async def log_out(bot: Bot) -> bool:
    return await bot.log_out()


async def check_if_logged_in(bot: Bot) -> bool:
    try:
        user = await bot.get_me()
    except BadRequest:
        return False

    if isinstance(user, User):
        return True
    elif user is None:
        return False
    else:
        raise Exception("An error occurred while trying to get the bot's user.")


async def log_out_if_logged_in(bot: Bot):
    logged_in = await check_if_logged_in(bot)

    if logged_in:
        print("User is logged in. Logging out...")
        await log_out(bot)

        print("Checking if logged out out...")
        logged_in = await check_if_logged_in(bot)

        if not logged_in:
            print("Logged out successfully.")
        else:
            raise Exception("An error occurred while trying to log out.")
    else:
        print("User is already logged out.")


if __name__ == '__main__':
    load_dotenv()

    TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
    application = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()
    asyncio.run(log_out_if_logged_in(application.bot))
    asyncio.run(application.bot.close())
