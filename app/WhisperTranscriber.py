import openai
import os
from dotenv import load_dotenv

# load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# set OPENAI_API_KEY as OpenAI key
openai.api_key = OPENAI_API_KEY


class WhisperTranscriber:
    SUPPORTED_EXTENSIONS = [".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"]
    MAX_FILE_SIZE_MB = 25

    @classmethod
    def is_file_supported(cls, audio_file_path) -> bool:
        _, file_ext = os.path.splitext(audio_file_path)
        return file_ext in cls.SUPPORTED_EXTENSIONS

    @classmethod
    def is_file_size_acceptable(cls, audio_file_path) -> bool:
        file_size_mb = os.path.getsize(audio_file_path) / (1024 * 1024)
        return file_size_mb <= cls.MAX_FILE_SIZE_MB

    @classmethod
    def validate_file(cls, audio_file_path) -> bool:
        if not cls.is_file_supported(audio_file_path):
            print(f"The file extension '{os.path.splitext(audio_file_path)[1]}' is not supported.")
            return False
        if not cls.is_file_size_acceptable(audio_file_path):
            print(f"The provided file '{audio_file_path}' is too large (> {cls.MAX_FILE_SIZE_MB}MB).")
            return False
        return True

    @staticmethod
    def transcribe_audio(audio_file_path) -> str:
        if not WhisperTranscriber.validate_file(audio_file_path):
            raise Exception("The provided file is not valid.")

        with open(audio_file_path, "rb") as audio_file:
            try:
                response = openai.Audio.transcribe("whisper-1", audio_file)
                return response['text']
            except Exception as e:
                raise Exception(f"An exception occurred while trying to transcribe the audio: {e}")
