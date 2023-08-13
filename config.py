import os

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
WAV_SAMPLING_RATE = 16000
MIN_CHUNK_DURATION_S = 1 * 60
MAX_CHUNK_DURATION_S = 4 * 60
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
