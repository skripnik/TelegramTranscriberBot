import os

from config import DATA_DIR


class UserMediaModel:
    def __init__(self, user_id, message_id):
        self.folder = f"{DATA_DIR}/{user_id}/{message_id}"
        self.original_file = None
        self.wav_file = f"{self.folder}/converted.wav"
        self.mp3_file = f"{self.folder}/converted.mp3"
        self.audacity_speech_labels = f"{self.folder}/audacity_speech.txt"
        self.audacity_chunk_labels = f"{self.folder}/audacity_chunks.txt"

        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

    def save_user_media(self, file_contents: bytearray, file_extension):
        self.original_file = f"{self.folder}/original.{file_extension}"

        with open(self.original_file, "wb") as file:
            file.write(file_contents)

    def get_original_file(self):
        if self.original_file is None:
            for file in os.listdir(self.folder):
                if file.startswith("original."):
                    self.original_file = f"{self.folder}/{file}"
                    break

        if self.original_file is None:
            raise FileNotFoundError(f"Original media file not found.")

        if not os.path.exists(self.original_file):
            raise FileNotFoundError(f"File {self.original_file} not found.")

        return self.original_file

    def get_wav_version(self):
        if not os.path.exists(self.wav_file):
            raise FileNotFoundError(f"File {self.wav_file} not found.")

        return self.wav_file

    def get_mp3_version(self):
        if not os.path.exists(self.mp3_file):
            raise FileNotFoundError(f"File {self.mp3_file} not found.")

        return self.mp3_file
