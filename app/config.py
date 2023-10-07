import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
WAV_SAMPLING_RATE = 16000  # Silero can only work with 16000 or 8000
MIN_CHUNK_DURATION_S = 1 * 60
MAX_CHUNK_DURATION_S = 3 * 60
TRANSCRIPTION_PREVIEW_CHARS = 200

TELEGRAM_BASE_URL = os.environ.get("TELEGRAM_BASE_URL", "http://localhost:8081/bot")
TELEGRAM_BASE_FILE_URL = os.environ.get(
    "TELEGRAM_BASE_FILE_URL", "http://localhost:8081/file/bot"
)
