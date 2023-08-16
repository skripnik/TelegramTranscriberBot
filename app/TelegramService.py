import os

from dotenv import load_dotenv
from telegram import Update, Message, User
from telegram.error import BadRequest
from telegram.ext import MessageHandler, filters, ContextTypes, CommandHandler, AIORateLimiter, ApplicationBuilder
from telegram.constants import MessageLimit
from ChunkProcessor import ChunkProcessor
from MediaConverter import MediaConverter
from models.MediaFileModel import MediaFileModel
from WhisperTranscriber import WhisperTranscriber
from models.UserModel import UserModel
from config import ALLOWED_TELEGRAM_CHAT_IDS, TRANSCRIPTION_PREVIEW_CHARS, MAX_CHUNK_DURATION_S, DATA_DIR, \
    TELEGRAM_BASE_URL, TELEGRAM_BASE_FILE_URL


class TelegramService:
    def __init__(self):
        load_dotenv()
        self.TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
        self.application = None

    def build_app(self, local_mode: bool):
        application_builder = ApplicationBuilder()
        application_builder.token(self.TELEGRAM_API_TOKEN)

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
        application = application_builder.build()

        self.application = application

    async def log_out(self) -> bool:
        return await self.application.bot.log_out()

    async def check_if_logged_in(self) -> bool:
        try:
            user = await self.application.bot.get_me()
        except BadRequest:
            return False

        if isinstance(user, User):
            return True
        elif user is None:
            return False
        else:
            raise Exception("An error occurred while trying to get the bot's user.")

    async def log_out_if_logged_in(self):
        logged_in = await self.check_if_logged_in()

        if logged_in:
            print("User is logged in. Logging out...")
            await self.log_out()

            print("Checking if logged out out...")
            logged_in = await self.check_if_logged_in()

            if not logged_in:
                print("Logged out successfully.")
            else:
                raise Exception("An error occurred while trying to log out.")
        else:
            print("User is already logged out.")

    async def close_and_log_out(self):
        await self.application.bot.close()
        await self.log_out_if_logged_in()

    def run_polling(self):
        self.application.run_polling()

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_first_name = update.effective_user.first_name
        start_message = f"Hello, {user_first_name}!\n" \
                        f"Send me an audio, voice or video and I'll transcribe it for you."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=start_message)

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message
        user_id = user_message.from_user.id if user_message.from_user is not None else "0"
        chat_id = user_message.chat.id

        media_file = MediaFileModel(user_id, user_message.message_id, DATA_DIR)

        # check ALLOWED_TELEGRAM_CHAT_IDS
        if chat_id not in ALLOWED_TELEGRAM_CHAT_IDS:
            reply = f"This bot is limited to certain chats only.\n" \
                    f"Please ask the admin to add this chat ID to the list: {chat_id}"
            await context.bot.send_message(
                chat_id=chat_id,
                text=reply,
                reply_to_message_id=user_message.message_id
            )
            return

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
        elif user_message.forward_from_message_id is not None and user_message.forward_from_chat is not None:
            reply = "I don't know how to work with forwarded messages yet."
            await context.bot.send_message(
                chat_id=chat_id,
                text=reply,
                reply_to_message_id=user_message.message_id
            )
            return
        else:
            reply = "I don't recognize this media type.\n" \
                    "If you send me audio, voice or video, i'll transcribe it."
            await context.bot.send_message(
                chat_id=chat_id,
                text=reply,
                reply_to_message_id=user_message.message_id
            )
            return

        # Check permissions
        message_text = f"Checking permissions..."
        main_reply = await context.bot.send_message(
            chat_id=chat_id,
            text=message_text,
            reply_to_message_id=user_message.message_id
        )
        user_model = UserModel(user_id, DATA_DIR)
        user_model.save_user_info(update.effective_user)

        # Download the file
        await main_reply.edit_text(f"Downloading {media_file.original_file_type}...")

        try:
            file = await self.application.bot.get_file(media_file.original_file_id)
        except Exception as e:
            await main_reply.edit_text(f"Error getting file info:\n{e}\n\nFile ID:\n{media_file.original_file_id}")
            return

        try:
            file_contents = await file.download_as_bytearray()
        except Exception as e:
            await main_reply.edit_text(f"Error downloading file:\n{e}\n\nFile ID:\n{media_file.original_file_id}")
            return

        media_file.original_file_extension = file.file_path.split(".")[-1]

        try:
            media_file.save_user_media(file_contents)
        except Exception as e:
            await main_reply.edit_text(f"Error saving file: {e}")
            return

        if media_file.original_file_duration_s <= MAX_CHUNK_DURATION_S:
            await self.handle_short_audio(media_file, main_reply)
        else:
            await self.handle_long_audio(media_file, main_reply)

        media_file.delete()

    @staticmethod
    async def handle_short_audio(media_file: MediaFileModel, main_reply: Message):
        original_file_location = media_file.original_file_location
        if WhisperTranscriber.validate_file(original_file_location):
            audio_source = original_file_location
        else:
            await main_reply.edit_text("Converting audio to MP3...")
            mp3_file_location = media_file.mp3_file

            try:
                MediaConverter.convert_to_mp3(original_file_location, mp3_file_location)
            except Exception as e:
                await main_reply.edit_text(f"Error converting file to MP3: {e}")
                return

            if WhisperTranscriber.validate_file(mp3_file_location):
                audio_source = mp3_file_location
            else:
                await main_reply.edit_text("Converted MP3 file is still not valid for Whisper.")
                return

        await main_reply.edit_text("Transcribing audio with Whisper...")
        try:
            transcription = WhisperTranscriber.transcribe_audio(audio_source)
        except Exception as e:
            await main_reply.edit_text(f"Error transcribing audio:\n{e}")
            return

        media_file.save_transcription([transcription])

        if len(transcription) > MessageLimit.MAX_TEXT_LENGTH:
            await main_reply.edit_text("Your transcription is ready:")
            await main_reply.reply_document(
                document=open(media_file.transcription_file, 'rb'),
                caption=transcription[:TRANSCRIPTION_PREVIEW_CHARS] + "...",
                reply_to_message_id=main_reply.reply_to_message.message_id
            )
        else:
            await main_reply.edit_text(transcription)

    @staticmethod
    async def handle_long_audio(media_file: MediaFileModel, main_reply: Message):
        transcriptions = []

        await main_reply.edit_text("Converting audio to WAV (PCM)...")
        original_file_location = media_file.original_file_location
        pcm_wav_file_location = media_file.pcm_wav_file

        try:
            MediaConverter.convert_to_pcm_wav(original_file_location, pcm_wav_file_location)
        except Exception as e:
            await main_reply.edit_text(f"Error converting file to WAV (PCM): {e}")
            return

        await main_reply.edit_text("Detecting speech...")
        try:
            silero_timestamps = ChunkProcessor.detect_timestamps(pcm_wav_file_location)
        except Exception as e:
            await main_reply.edit_text(f"Error detecting speech: {e}")
            return

        chunks = ChunkProcessor.calculate_chunks(silero_timestamps, media_file.original_file_duration_s)
        chunks_found = len(chunks)

        await main_reply.edit_text(f"Splitting audio in {chunks_found} chunks...")
        try:
            ChunkProcessor.split_audio_into_chunks(chunks, media_file)
        except Exception as e:
            await main_reply.edit_text(f"Error splitting audio: {e}")
            return

        await main_reply.edit_text(f"Transcribing {chunks_found} chunks:")

        for i in range(chunks_found):
            chunk_path = media_file.get_chunk_location(i)
            with open(chunk_path, 'rb') as audio:
                await main_reply.reply_audio(
                    audio=audio,
                    title=f"Chunk {i + 1} of {chunks_found}",
                    performer="Transcription",
                    disable_notification=True
                )

            chunk_message = await main_reply.reply_text(
                text=f"Transcribing chunk {i + 1} of {chunks_found}...",
                disable_notification=True,
            )

            try:
                transcription = WhisperTranscriber.transcribe_audio(chunk_path)
            except Exception as e:
                await chunk_message.edit_text(f"Error transcribing chunk {i + 1} of {chunks_found}: {e}")
                return

            transcriptions.append(transcription)
            await chunk_message.edit_text(transcription)

        media_file.save_transcription(transcriptions)

        await main_reply.reply_document(
            document=open(media_file.transcription_file, 'rb'),
            caption=transcriptions[0][:TRANSCRIPTION_PREVIEW_CHARS] + "...",
            reply_to_message_id=main_reply.reply_to_message.message_id
        )

    def setup(self):
        start_handler = CommandHandler('start', self.start)
        self.application.add_handler(start_handler)

        audio_handler = MessageHandler(~filters.COMMAND, self.message)
        self.application.add_handler(audio_handler)
