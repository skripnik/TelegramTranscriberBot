from telegram import Update, Message
from telegram.ext import MessageHandler, filters, ContextTypes, CommandHandler
from ChunkProcessor import ChunkProcessor
from MediaConverter import MediaConverter
from models.MediaFileModel import MediaFileModel
from WhisperTranscriber import WhisperTranscriber
from models.UserModel import UserModel
from config import TELEGRAM_MAX_MESSAGE_LENGTH, ALLOWED_TELEGRAM_CHAT_IDS


class TelegramService:
    def __init__(self, application):
        self.application = application

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
            file_id = user_message.audio.file_id
            file_type = "audio"
        elif user_message.voice is not None:
            file_id = user_message.voice.file_id
            file_type = "voice"
        elif user_message.video is not None:
            file_id = user_message.video.file_id
            file_type = "video"
        elif user_message.video_note is not None:
            file_id = user_message.video_note.file_id
            file_type = "video note"
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
        user_model = UserModel(user_id)
        user_model.save_user_info(update.effective_user)

        # Download the file
        message_text = f"Downloading {file_type}..."
        await main_reply.edit_text(message_text)

        try:
            media_file = MediaFileModel(user_id, user_message.message_id)
            file = await self.application.bot.get_file(file_id)
            file_extension = file.file_path.split(".")[-1]
            file_contents = await file.download_as_bytearray()
            media_file.save_user_media(file_contents, file_extension)
        except Exception as e:
            await main_reply.edit_text(f"Error downloading file: {e}")
            return

        original_file_location = media_file.get_original_file_location()

        # Can we send it right away to Whisper?
        if WhisperTranscriber.validate_file(original_file_location):
            await self.handle_simple_audio(original_file_location, main_reply, user_message, media_file)
            return

        # If not, let's try to convert it to mp3 and check it again
        await main_reply.edit_text("Converting audio...")
        mp3_file_location = media_file.get_mp3_location()
        try:
            MediaConverter.convert_to_mp3(original_file_location, mp3_file_location)
        except Exception as e:
            await main_reply.edit_text(f"Error converting file: {e}")
            return

        if WhisperTranscriber.validate_file(mp3_file_location):
            await self.handle_simple_audio(mp3_file_location, main_reply, user_message, media_file)
            return

        # Well, at this point let's split it into chunks
        pcm_wav_file_location = media_file.get_pcm_wav_location()
        try:
            MediaConverter.convert_to_pcm_wav(original_file_location, pcm_wav_file_location)
        except Exception as e:
            await main_reply.edit_text(f"Error converting file: {e}")
            return

        await main_reply.edit_text("Detecting speech...")
        try:
            silero_timestamps = ChunkProcessor.detect_timestamps(pcm_wav_file_location)
        except Exception as e:
            await main_reply.edit_text(f"Error detecting speech: {e}")
            return

        chunks = ChunkProcessor.calculate_chunks(silero_timestamps)
        chunks_found = len(chunks)

        if chunks_found == 1:
            await self.handle_simple_audio(original_file_location, main_reply, user_message, media_file)
            return
        else:
            transcriptions = []

            await main_reply.edit_text("Splitting audio in chunks...")
            try:
                ChunkProcessor.split_audio_into_chunks(chunks, media_file)
            except Exception as e:
                await main_reply.edit_text(f"Error splitting audio: {e}")
                return

            for i in range(chunks_found):
                await main_reply.edit_text(f"Transcribing chunk {i + 1} of {chunks_found}...")

                chunk_path = media_file.get_chunk_location(i)
                try:
                    transcription = WhisperTranscriber.transcribe_audio(chunk_path)
                except Exception as e:
                    await main_reply.edit_text(f"Error transcribing chunk {i + 1} of {chunks_found}: {e}")
                    return

                transcriptions.append(transcription)

                with open(chunk_path, 'rb') as audio:
                    await context.bot.send_audio(
                        chat_id=update.effective_chat.id,
                        audio=audio,
                        title=f"Part {i + 1} of {chunks_found}"
                    )

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=transcription
                )

            transcription = "\n\n".join(transcriptions)
            await main_reply.reply_document(
                document=open(media_file.get_transcription_location(), 'rb'),
                caption=transcription[:300] + "...",
                reply_to_message_id=user_message.message_id
            )

    @staticmethod
    async def handle_simple_audio(original_file_location: str, reply_message: Message, user_message: Message,
                                  media_file: MediaFileModel):
        await reply_message.edit_text("Transcribing audio...")
        try:
            transcription = WhisperTranscriber.transcribe_audio(original_file_location)
        except Exception as e:
            await reply_message.edit_text(f"Error transcribing audio: {e}")
            return

        media_file.save_transcription(transcription)

        if len(transcription) > TELEGRAM_MAX_MESSAGE_LENGTH:
            await reply_message.edit_text("Your transcription is ready:")
            await reply_message.reply_document(
                document=open(media_file.get_transcription_location(), 'rb'),
                caption=transcription[:300] + "...",
                reply_to_message_id=user_message.message_id
            )
        else:
            await reply_message.edit_text(transcription)

    def setup(self):
        start_handler = CommandHandler('start', self.start)
        self.application.add_handler(start_handler)

        audio_handler = MessageHandler(~filters.COMMAND, self.message)
        self.application.add_handler(audio_handler)

        return self
