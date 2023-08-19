from telegram import Update, Message, Bot
from telegram.ext import (
    MessageHandler,
    filters,
    CommandHandler,
    AIORateLimiter,
    ApplicationBuilder,
    Application,
    CallbackContext,
)
from telegram.constants import MessageLimit

from app.TelegramPermissionChecker import TelegramPermissionChecker
from app.chunk_processor import (
    detect_timestamps,
    calculate_chunks,
    split_audio_into_chunks,
)
from app.media_converter import convert_to_mp3, convert_to_pcm_wav
from models.MediaFileModel import MediaFileModel
from WhisperTranscriber import WhisperTranscriber
from models.UserModel import UserModel
from config import (
    TRANSCRIPTION_PREVIEW_CHARS,
    MAX_CHUNK_DURATION_S,
    DATA_DIR,
    TELEGRAM_BASE_URL,
    TELEGRAM_BASE_FILE_URL,
)


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
            filters.AUDIO | filters.VIDEO | filters.VOICE | filters.VIDEO_NOTE,
            self._handle_media,
        )

        self.application.add_handlers(
            [start_handler, media_handler, text_handler, forwarded_handler]
        )

        self.application.run_polling()

    async def _check_chat_access(self, update: Update) -> Message | None:
        user_id = update.message.from_user.id
        chat_id = update.message.chat.id

        main_reply = await update.message.reply_text(
            "Checking permissions...",
            quote=True,
        )

        permission_checker = TelegramPermissionChecker(self.bot)

        try:
            is_allowed_chat = await permission_checker.is_user_or_group_allowed(
                user_id, chat_id
            )
        except Exception as e:
            await main_reply.edit_text(f"Error checking permissions:\n{e}")
            return None

        if not is_allowed_chat:
            reply = (
                "This bot is limited to certain chats only.\n"
                "Please ask the admin to add you to some private group "
                f"or to add this chat ID to the list of allowed chats: {chat_id}"
            )
            await main_reply.edit_text(reply)
            return None

        return main_reply

    async def _handle_start_command(self, update: Update, context: CallbackContext):
        main_reply = await self._check_chat_access(update)
        if main_reply is None:
            return

        user_first_name = update.effective_user.first_name
        start_message = (
            f"Hello, {user_first_name}!\n"
            f"Send me an audio, voice or video and I'll transcribe it for you."
        )
        await main_reply.edit_text(start_message)

    async def _handle_text_message(
        self, update: Update, context: CallbackContext
    ) -> None:
        main_reply = await self._check_chat_access(update)
        if main_reply is None:
            return

        reply = (
            "I don't recognize text messages.\n"
            "If you send me audio, voice or video, i'll transcribe it."
        )
        await update.message.reply_text(reply)

    async def _handle_forwarded_message(
        self, update: Update, context: CallbackContext
    ) -> None:
        main_reply = await self._check_chat_access(update)
        if main_reply is None:
            return

        reply = "I don't know how to work with forwarded messages yet."
        await update.message.reply_text(reply)

    async def _handle_media(self, update: Update, context: CallbackContext) -> None:
        # Check permissions
        main_reply = await self._check_chat_access(update)
        if main_reply is None:
            return

        user_message = update.message
        user_id = user_message.from_user.id
        user_model = UserModel(user_id, DATA_DIR)
        user_model.save_user_info(update.effective_user)

        media_file = MediaFileModel(user_id, user_message.message_id, DATA_DIR)
        if user_message.audio is not None:
            media_file.original_file_id = user_message.audio.file_id
            media_file.original_file_duration_s = user_message.audio.duration
            media_file.original_file_type = "audio"
        elif user_message.voice is not None:
            media_file.original_file_id = user_message.voice.file_id
            media_file.original_file_duration_s = user_message.voice.duration
            media_file.original_file_type = "voice"
        elif user_message.video is not None:
            media_file.original_file_id = user_message.video.file_id
            media_file.original_file_duration_s = user_message.video.duration
            media_file.original_file_type = "video"
        elif user_message.video_note is not None:
            media_file.original_file_id = user_message.video_note.file_id
            media_file.original_file_duration_s = user_message.video_note.duration
            media_file.original_file_type = "video note"

        # Download the file
        await main_reply.edit_text(f"Downloading {media_file.original_file_type}...")

        try:
            file = await self.bot.get_file(media_file.original_file_id)
        except Exception as e:
            await main_reply.edit_text(
                f"Error getting file info:\n{e}\n\n"
                f"File ID:\n{media_file.original_file_id}"
            )
            return

        try:
            file_contents = await file.download_as_bytearray()
        except Exception as e:
            await main_reply.edit_text(
                f"Error downloading file:\n{e}\n\n"
                f"File ID:\n{media_file.original_file_id}"
            )
            return

        media_file.original_file_extension = file.file_path.split(".")[-1]

        try:
            media_file.save_user_media(file_contents)
        except Exception as e:
            await main_reply.edit_text(f"Error saving file: {e}")
            return

        if media_file.original_file_duration_s <= MAX_CHUNK_DURATION_S:
            await self._transcribe_short_audio(media_file, main_reply)
        else:
            await self._transcribe_long_audio(media_file, main_reply)

        # TODO: make it right way, it doesn't delete the file if there is an exception
        media_file.destroy()

    @staticmethod
    async def _transcribe_short_audio(media_file: MediaFileModel, main_reply: Message):
        original_file_location = media_file.original_file_location
        if WhisperTranscriber.validate_file(original_file_location):
            audio_source = original_file_location
        else:
            await main_reply.edit_text("Converting audio to MP3...")
            mp3_file_location = media_file.mp3_file

            try:
                convert_to_mp3(original_file_location, mp3_file_location)
            except Exception as e:
                await main_reply.edit_text(f"Error converting file to MP3: {e}")
                return

            if WhisperTranscriber.validate_file(mp3_file_location):
                audio_source = mp3_file_location
            else:
                await main_reply.edit_text(
                    "Converted MP3 file is still not valid for Whisper."
                )
                return

        await main_reply.edit_text("Transcribing audio with Whisper...")
        try:
            transcription = WhisperTranscriber.transcribe_audio(audio_source)
        except Exception as e:
            await main_reply.edit_text(f"Error transcribing audio:\n{e}")
            return

        if not transcription:
            await main_reply.edit_text("Transcription is empty.")
            return

        media_file.save_transcription([transcription])

        if len(transcription) > MessageLimit.MAX_TEXT_LENGTH:
            await main_reply.edit_text("Your transcription is ready:")
            await main_reply.reply_document(
                document=open(media_file.transcription_file, "rb"),
                caption=transcription[:TRANSCRIPTION_PREVIEW_CHARS] + "...",
                reply_to_message_id=main_reply.reply_to_message.message_id,
            )
        else:
            await main_reply.edit_text(transcription)

    @staticmethod
    async def _transcribe_long_audio(media_file: MediaFileModel, main_reply: Message):
        transcriptions = []

        await main_reply.edit_text("Converting audio to WAV (PCM)...")
        original_file_location = media_file.original_file_location
        pcm_wav_file_location = media_file.pcm_wav_file

        try:
            convert_to_pcm_wav(original_file_location, pcm_wav_file_location)
        except Exception as e:
            await main_reply.edit_text(f"Error converting file to WAV (PCM): {e}")
            return

        await main_reply.edit_text("Detecting speech...")
        try:
            silero_timestamps = detect_timestamps(pcm_wav_file_location)
        except Exception as e:
            await main_reply.edit_text(f"Error detecting speech: {e}")
            return

        chunks = calculate_chunks(
            silero_timestamps, media_file.original_file_duration_s
        )
        chunks_found = len(chunks)

        await main_reply.edit_text(f"Splitting audio in {chunks_found} chunks...")
        try:
            split_audio_into_chunks(chunks, media_file)
        except Exception as e:
            await main_reply.edit_text(f"Error splitting audio: {e}")
            return

        await main_reply.edit_text(f"Transcribing {chunks_found} chunks:")

        for i in range(chunks_found):
            chunk_path = media_file.get_chunk_location(i)
            with open(chunk_path, "rb") as audio:
                await main_reply.reply_audio(
                    audio=audio,
                    title=f"Chunk {i + 1} of {chunks_found}",
                    performer="Transcription",
                    disable_notification=True,
                    reply_to_message_id=None,
                )

            chunk_message = await main_reply.reply_text(
                text=f"Transcribing chunk {i + 1} of {chunks_found}...",
                disable_notification=True,
                reply_to_message_id=None,
            )

            try:
                transcription = WhisperTranscriber.transcribe_audio(chunk_path)
            except Exception as e:
                await chunk_message.edit_text(
                    f"Error transcribing chunk {i + 1} of {chunks_found}: {e}"
                )
                return

            transcriptions.append(transcription)
            await chunk_message.edit_text(transcription)

        media_file.save_transcription(transcriptions)

        await main_reply.reply_document(
            document=open(media_file.transcription_file, "rb"),
            caption=transcriptions[0][:TRANSCRIPTION_PREVIEW_CHARS] + "...",
        )
