from telegram import Update, Message
from telegram.ext import MessageHandler, filters, ContextTypes
from app.ChunkProcessor import ChunkProcessor
from app.MediaConverter import MediaConverter
from app.models.MediaFileModel import MediaFileModel
from app.WhisperTranscriber import WhisperTranscriber
from app.models.UserModel import UserModel
from config import TELEGRAM_MAX_MESSAGE_LENGTH


class TelegramService:
    def __init__(self, application):
        self.application = application

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        user_id = update.effective_user.id if update.effective_user is not None else "0"
        chat_id = update.effective_chat.id

        if update.message.audio is not None:
            file_id = update.message.audio.file_id
            file_type = "audio"
        elif update.message.voice is not None:
            file_id = update.message.voice.file_id
            file_type = "voice"
        elif update.message.video is not None:
            file_id = update.message.video.file_id
            file_type = "video"
        else:
            reply = "If you send me audio, voice or video, i'll transcribe it."
            await context.bot.send_message(chat_id=chat_id, text=reply)
            return

        # Check permissions
        message_text = f"Checking permissions..."
        main_reply = await context.bot.send_message(chat_id=chat_id, text=message_text)
        user_model = UserModel(user_id)
        user_model.save_user_info(update.effective_user)

        # Download the file
        message_text = f"Downloading {file_type}..."
        await main_reply.edit_text(message_text)

        try:
            media_file = MediaFileModel(user_id, update.message.message_id)
            file = await self.application.bot.get_file(file_id)
            file_extension = file.file_path.split(".")[-1]
            file_contents = await file.download_as_bytearray()
            media_file.save_user_media(file_contents, file_extension)
        except Exception as e:
            await main_reply.edit_text(f"Error downloading file: {e}")
            return

        # Can we send it right away to Whisper?
        original_file_location = media_file.get_original_file_location()
        if WhisperTranscriber.validate_file(original_file_location):
            await self.handle_simple_audio(original_file_location, main_reply, media_file)
            return

        # If not, let's try to convert it to mp3 and check it again
        if not WhisperTranscriber.is_file_supported(original_file_location):
            await main_reply.edit_text("Converting audio...")
            mp3_file_location = media_file.get_mp3_location()
            MediaConverter.convert_to_mp3(original_file_location, mp3_file_location)

            if WhisperTranscriber.validate_file(mp3_file_location):
                await self.handle_simple_audio(mp3_file_location, main_reply, media_file)
                return

        # Well, at this point let's split it into chunks
        pcm_wav_file_location = media_file.get_pcm_wav_location()
        MediaConverter.convert_to_pcm_wav(original_file_location, pcm_wav_file_location)

        await main_reply.edit_text("Detecting speech...")
        silero_timestamps = ChunkProcessor.detect_timestamps(pcm_wav_file_location)
        chunks = ChunkProcessor.calculate_chunks(silero_timestamps)
        chunks_found = len(chunks)

        if chunks_found == 1:
            await self.handle_simple_audio(original_file_location, main_reply, media_file)
            return
        else:
            await main_reply.edit_text("Splitting audio in chunks...")
            ChunkProcessor.split_audio_into_chunks(chunks, media_file)

            for i in range(chunks_found):
                await main_reply.edit_text(f"Transcribing chunk {i + 1} of {chunks_found}...")

                chunk_path = media_file.get_chunk_location(i)
                transcription = WhisperTranscriber.transcribe_audio(chunk_path)

                with open(chunk_path, 'rb') as audio:
                    await context.bot.send_audio(
                        chat_id=update.effective_chat.id,
                        audio=audio,
                        title=f"Part {i + 1} of {chunks_found}"
                    )

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=transcription)

    @staticmethod
    async def handle_simple_audio(original_file_location: str, main_reply: Message, media_file: MediaFileModel):
        await main_reply.edit_text("Transcribing audio...")
        transcription = WhisperTranscriber.transcribe_audio(original_file_location)
        media_file.save_transcription(transcription)

        if len(transcription) > TELEGRAM_MAX_MESSAGE_LENGTH:
            await main_reply.edit_text("Your transcription is ready:")
            await main_reply.reply_document(
                document=open(media_file.get_transcription_location(), 'rb'),
                caption=transcription[:300] + "..."
            )
        else:
            await main_reply.edit_text(transcription)

    def setup(self):
        audio_handler = MessageHandler(~filters.COMMAND, self.message)
        self.application.add_handler(audio_handler)

        return self
