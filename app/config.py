import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')
WAV_SAMPLING_RATE = 16000
MIN_CHUNK_DURATION_S = 1 * 60
MAX_CHUNK_DURATION_S = 3 * 60
TRANSCRIPTION_PREVIEW_CHARS = 200

TELEGRAM_BASE_URL = "http://localhost:8081/bot"
TELEGRAM_BASE_FILE_URL = "http://localhost:8081/file/bot"

ALLOWED_TELEGRAM_CHAT_IDS = [
    -951184410,  # testing group with hackathon participants
    -1001985729384,  # private group with @UgaChaka
]
MEMBER_LIST_CACHE_TIME_SECONDS = 300  # 5 minutes
