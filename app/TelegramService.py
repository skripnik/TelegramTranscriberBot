from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
from app.AudioProcessor import AudioProcessor
from app.WhisperTranscriber import WhisperTranscriber
from config import DATA_DIR


class TelegramService:
    def __init__(self, application):
        self.application = application

    async def download_media(self, file_id, file_type):
        file = await self.application.bot.get_file(file_id)
        file_extension = file.file_path.split(".")[-1]
        target_file = f"{DATA_DIR}/converted_files/{file_type}/{file_id}.{file_extension}"
        await file.download_to_drive(target_file)
        return target_file, file_extension

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

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
            file_id = None
            file_type = None

        if file_id is None:
            reply = "Please send me an audio, voice or video file to transcribe."
            await context.bot.send_message(chat_id=update.effective_chat.id, text=reply)
            return

        message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Downloading {file_type}...")

        target_file, file_extension = await self.download_media(file_id, file_type)

        await message.edit_text("Converting audio...")
        audio_processor = AudioProcessor(target_file, file_id)
        audio_processor.convert_to_wav()

        await message.edit_text("Detecting speech...")
        audio_processor.detect_chapters()
        audio_processor.generate_audacity_speech_labels()
        audio_processor.generate_audacity_chunk_labels()

        chunks_found = len(audio_processor.chunks)

        if chunks_found == 1:
            await message.edit_text("Transcribing audio...")
            transcription = WhisperTranscriber.transcribe_audio(target_file)
            await message.edit_text(transcription)
        else:
            await message.edit_text("Splitting audio in chunks...")
            audio_processor.split_audio_into_chunks()

            for i in range(chunks_found):
                await message.edit_text(f"Transcribing chunk {i + 1} of {chunks_found}...")

                chunk_path = f"{DATA_DIR}/converted_files/{file_id}/chunk_{i}.mp3"
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

    def setup(self):
        audio_handler = MessageHandler(~filters.COMMAND, self.message)
        self.application.add_handler(audio_handler)

        return self
