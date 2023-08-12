import openai
import os
from dotenv import load_dotenv

# load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# set OPENAI_API_KEY as OpenAI key
openai.api_key = OPENAI_API_KEY


class WhisperTranscriber:
    @staticmethod
    def transcribe_audio(audio_file_path):
        with open(audio_file_path, "rb") as audio_file:
            try:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)
                return transcript['text']
            except Exception as e:
                print("An exception occurred while trying to transcribe the audio: {}".format(e))
                return None
