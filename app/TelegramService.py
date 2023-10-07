from telegram import Update, Bot
from telegram.ext import (
    MessageHandler,
    filters,
    CommandHandler,
    AIORateLimiter,
    ApplicationBuilder,
    Application,
    CallbackContext,
)
from app.TelegramTask import TelegramTask
from app.config import TELEGRAM_BASE_URL, TELEGRAM_BASE_FILE_URL


class TelegramService:
    def __init__(self, telegram_api_token: str, local_mode: bool):
        self.TELEGRAM_API_TOKEN: str = telegram_api_token
        self.application: Application = self._build_application(
            telegram_api_token=self.TELEGRAM_API_TOKEN, local_mode=local_mode
        )
        self.bot: Bot = self.application.bot

    @staticmethod
    def _build_application(telegram_api_token: str, local_mode: bool) -> Application:
        application_builder = ApplicationBuilder()
        application_builder.token(telegram_api_token)

        if local_mode:
            application_builder.base_url(TELEGRAM_BASE_URL)
            application_builder.base_file_url(TELEGRAM_BASE_FILE_URL)
            application_builder.local_mode(True)
        else:
            application_builder.local_mode(False)

        application_builder.read_timeout(30)
        application_builder.write_timeout(30)
        application_builder.connect_timeout(30)
        application_builder.pool_timeout(30)

        rate_limiter = AIORateLimiter(
            overall_max_rate=30,
            overall_time_period=1,
            group_max_rate=20,
            group_time_period=60,
            max_retries=3,
        )

        application_builder.rate_limiter(rate_limiter)
        application: Application = application_builder.build()

        return application

    def setup_handlers(self):
        start_handler = CommandHandler("start", self._handle_start_command)

        text_handler = MessageHandler(
            filters.TEXT & ~filters.COMMAND, self._handle_text_message
        )

        forwarded_handler = MessageHandler(
            filters.FORWARDED, self._handle_forwarded_message
        )

        media_handler = MessageHandler(
            filters.AUDIO
            | filters.VIDEO
            | filters.VOICE
            | filters.VIDEO_NOTE
            | filters.Document.ALL,
            self._handle_media,
        )

        self.application.add_handlers(
            [start_handler, media_handler] # ,text_handler, forwarded_handler]
        )

        self.application.run_polling()

    async def _handle_start_command(self, update: Update, context: CallbackContext):
        task = TelegramTask(self.bot, update)
        if await task.is_allowed():
            await task.handle_start_command()

    async def _handle_text_message(
        self, update: Update, context: CallbackContext
    ) -> None:
        task = TelegramTask(self.bot, update)
        if await task.is_allowed():
            await task.handle_text_message()

    async def _handle_forwarded_message(
        self, update: Update, context: CallbackContext
    ) -> None:
        task = TelegramTask(self.bot, update)
        if await task.is_allowed():
            await task.handle_forwarded_message()

    async def _handle_media(self, update: Update, context: CallbackContext) -> None:
        task = TelegramTask(self.bot, update)
        if await task.is_allowed():
            await task.handle_media()
