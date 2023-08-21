from telegram import Message, Update, Bot, User
from telegram.constants import MessageLimit

from app.TelegramPermissionChecker import TelegramPermissionChecker
from app.WhisperTranscriber import WhisperTranscriber
from app.chunk_processor import (
    detect_timestamps,
    calculate_chunks,
    split_audio_into_chunks,
)
from app.config import DATA_DIR, MAX_CHUNK_DURATION_S, TRANSCRIPTION_PREVIEW_CHARS
from app.media_converter import convert_to_mp3, convert_to_pcm_wav, get_duration
from app.models.MediaFileModel import MediaFileModel
from app.models.UserModel import UserModel


class TelegramTask:
    def __init__(self, bot: Bot, update: Update):
        self.bot: Bot = bot
        self.user: User = update.effective_user
        self.user_message: Message = update.message
        self.first_reply: Message | None = None

    async def set_first_reply(self, reply_text: str) -> None:
        if self.first_reply:
            await self.first_reply.edit_text(reply_text)
            return

        if self.user_message is None:
            raise RuntimeError("⚠️ User message is not set.")

        self.first_reply = await self.user_message.reply_text(reply_text, quote=True)

    async def delete_first_reply(self) -> None:
        if self.first_reply:
            await self.first_reply.delete()

    async def is_allowed(self) -> bool:
        await self.set_first_reply("🔑 Checking permissions...")

        user_id: int = self.user_message.from_user.id
        chat_id: int = self.user_message.chat.id
        permission_checker = TelegramPermissionChecker(self.bot)

        if user_id == chat_id:
            decision: bool = await permission_checker.is_user_allowed(user_id)

            if decision is False:
                await self.set_first_reply(
                    f"⚠️ {self.user.first_name}, this bot is limited to certain "
                    f"users and groups only. Please ask the admin to add your "
                    f"user ID to the list of allowed chats.\n"
                    f"Your user ID: {user_id}"
                )
        else:
            decision: bool = await permission_checker.is_group_allowed(chat_id)

            if decision is False:
                await self.set_first_reply(
                    "⚠️ This bot is limited to certain groups only.\n"
                    "Please ask the admin to add this group ID to the list of allowed chats.\n"
                    f"This group ID: {chat_id}"
                )

        return decision

    async def handle_start_command(self):
        await self.set_first_reply(
            f"👋 Hello, {self.user.first_name}!\n"
            f"Send me an audio, voice or video and I'll transcribe it for you."
        )

    async def handle_text_message(self) -> None:
        await self.set_first_reply(
            "⚠️ I don't know what to do with text messages. "
            "If you send me audio, voice or video, i'll transcribe it."
        )

    async def handle_forwarded_message(self) -> None:
        await self.set_first_reply(
            "⚠️ I don't know how to work with forwarded messages yet."
        )

    async def download_file(self, media_file: MediaFileModel) -> None:
        await self.set_first_reply(f"📥 Downloading {media_file.original_file_type}...")

        try:
            file = await self.bot.get_file(media_file.original_file_id)
        except Exception as e:
            media_file.destroy()
            await self.set_first_reply(
                f"⚠️ Error getting file info:\n{e}\n\n"
                f"File ID:\n{media_file.original_file_id}"
            )
            return

        try:
            file_contents = await file.download_as_bytearray()
        except Exception as e:
            media_file.destroy()
            await self.set_first_reply(
                f"⚠️ Error downloading file:\n{e}\n\n"
                f"File ID:\n{media_file.original_file_id}"
            )
            return

        media_file.original_file_extension = file.file_path.split(".")[-1]

        try:
            media_file.save_user_media(file_contents)
        except Exception as e:
            media_file.destroy()
            await self.set_first_reply(f"⚠️ Error saving file:\n{e}")
            return

    async def handle_media(self) -> None:
        user_message = self.user_message
        user_id = user_message.from_user.id
        user_model = UserModel(user_id, DATA_DIR)
        user_model.save_user_info(self.user)

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
        elif user_message.document is not None:
            media_file.original_file_id = user_message.document.file_id
            media_file.original_file_duration_s = None
            media_file.original_file_type = "document"

        await self.download_file(media_file)

        if media_file.original_file_duration_s is None:
            try:
                media_file.original_file_duration_s = get_duration(
                    media_file.original_file_location
                )
            except Exception as e:
                await self.set_first_reply(
                    f"⚠️ Error getting duration of audio in the document:\n{e}"
                )
                return

        if media_file.original_file_duration_s <= MAX_CHUNK_DURATION_S:
            await self._transcribe_short_audio(media_file)
        else:
            await self._transcribe_long_audio(media_file)

        media_file.destroy()

    async def _transcribe_short_audio(self, media_file: MediaFileModel):
        original_file_location = media_file.original_file_location
        if WhisperTranscriber.validate_file(original_file_location):
            audio_source = original_file_location
        else:
            await self.set_first_reply("🎛️ Converting audio to MP3...")
            mp3_file_location = media_file.mp3_file

            try:
                convert_to_mp3(original_file_location, mp3_file_location)
            except Exception as e:
                await self.set_first_reply(f"⚠️ Error converting file to MP3: {e}")
                return

            if WhisperTranscriber.validate_file(mp3_file_location):
                audio_source = mp3_file_location
            else:
                await self.set_first_reply(
                    "⚠️ Converted MP3 file is still not valid for Whisper."
                )
                return

        await self.set_first_reply("✍️ Transcribing audio with Whisper...")
        try:
            transcription = WhisperTranscriber.transcribe_audio(audio_source)
        except Exception as e:
            await self.set_first_reply(f"⚠️ Error transcribing audio:\n{e}")
            return

        if not transcription:
            await self.set_first_reply("⚠️ Transcription is empty.")
            return

        media_file.save_transcription([transcription])

        if len(transcription) > MessageLimit.MAX_TEXT_LENGTH:
            await self.delete_first_reply()
            await self.user_message.reply_document(
                document=open(media_file.transcription_file, "rb"),
                caption=transcription[:TRANSCRIPTION_PREVIEW_CHARS] + "...",
                quote=True,
            )
        else:
            await self.set_first_reply(transcription)

    async def _transcribe_long_audio(self, media_file: MediaFileModel):
        transcriptions = []

        await self.set_first_reply("🎛️ Converting audio to WAV (PCM)...")
        original_file_location = media_file.original_file_location
        pcm_wav_file_location = media_file.pcm_wav_file

        try:
            convert_to_pcm_wav(original_file_location, pcm_wav_file_location)
        except Exception as e:
            await self.set_first_reply(f"⚠️ Error converting file to WAV (PCM): {e}")
            return

        await self.set_first_reply("🔍 Detecting speech...")
        try:
            silero_timestamps = detect_timestamps(pcm_wav_file_location)
        except Exception as e:
            await self.set_first_reply(f"⚠️ Error detecting speech: {e}")
            return

        chunks = calculate_chunks(
            silero_timestamps, media_file.original_file_duration_s
        )
        chunks_found = len(chunks)

        await self.set_first_reply(f"✂️ Splitting audio in {chunks_found} chunks...")
        try:
            split_audio_into_chunks(chunks, media_file)
        except Exception as e:
            await self.set_first_reply(f"⚠️ Error splitting audio: {e}")
            return

        await self.set_first_reply(f"Transcribing {chunks_found} chunks:")

        for i in range(chunks_found):
            chunk_path = media_file.get_chunk_location(i)
            with open(chunk_path, "rb") as audio:
                await self.user_message.reply_audio(
                    audio=audio,
                    title=f"Chunk {i + 1} of {chunks_found}",
                    performer="Transcription",
                    disable_notification=True,
                    reply_to_message_id=None,
                )

            chunk_message = await self.user_message.reply_text(
                text=f"✍️ Transcribing chunk {i + 1} of {chunks_found}...",
                disable_notification=True,
                reply_to_message_id=None,
            )

            try:
                transcription = WhisperTranscriber.transcribe_audio(chunk_path)
            except Exception as e:
                await chunk_message.edit_text(
                    f"⚠️ Error transcribing chunk {i + 1} of {chunks_found}: {e}"
                )
                return

            transcriptions.append(transcription)
            await chunk_message.edit_text(transcription)

        media_file.save_transcription(transcriptions)

        await self.user_message.reply_document(
            document=open(media_file.transcription_file, "rb"),
            caption=transcriptions[0][:TRANSCRIPTION_PREVIEW_CHARS] + "...",
            quote=True,
        )
