import os
import json

from config import DATA_DIR


class MediaFileModel:
    def __init__(self, user_id, message_id):
        self.folder = f"{DATA_DIR}/{user_id}/{message_id}"
        self.original_file = None
        self.pcm_wav_file = f"{self.folder}/converted.wav"
        self.mp3_file = f"{self.folder}/converted.mp3"
        self.audacity_speech_labels = f"{self.folder}/audacity_speech.txt"
        self.audacity_chunk_labels = f"{self.folder}/audacity_chunks.txt"
        self.silero_timestamps_json = f"{self.folder}/silero_timestamps.json"
        self.transcription_file = f"{self.folder}/transcription.txt"

    def save_user_media(self, file_contents: bytearray, file_extension):
        self.original_file = f"{self.folder}/original.{file_extension}"

        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

        with open(self.original_file, "wb") as file:
            file.write(file_contents)

    def get_original_file_location(self) -> str or None:
        return self.original_file

    def get_pcm_wav_location(self) -> str:
        return self.pcm_wav_file

    def get_mp3_location(self) -> str:
        return self.mp3_file

    def get_chunk_location(self, chunk_id):
        return f"{self.folder}/chunk_{chunk_id}.mp3"

    def save_silero_timestamps(self, timestamps: list):
        with open(self.silero_timestamps_json, "w") as file:
            json.dump(timestamps, file)

    def get_silero_timestamps(self) -> list:
        with open(self.silero_timestamps_json, "r") as file:
            return json.load(file)

    def save_audacity_speech_labels(self, silero_timestamps: list):
        formatted_lines = []

        for timestamps in silero_timestamps:
            start_time = format(timestamps['start'], '.3f')
            end_time = format(timestamps['end'], '.3f')
            label = "speech"
            formatted_line = f"{start_time}\t{end_time}\t{label}"
            formatted_lines.append(formatted_line)

        with open(self.audacity_speech_labels, "w") as file:
            file.write("\n".join(formatted_lines))

    def save_audacity_chunk_labels(self, chunks: list):
        formatted_lines = []

        for chunk in chunks:
            start_time = format(chunk[0], '.3f')
            end_time = format(chunk[1], '.3f')
            label = "chunk"
            formatted_line = f"{start_time}\t{end_time}\t{label}"
            formatted_lines.append(formatted_line)

        with open(self.audacity_chunk_labels, "w") as file:
            file.write("\n".join(formatted_lines))

    def save_transcription(self, transcription: str):
        with open(self.transcription_file, "w") as file:
            file.write(transcription)

    def get_transcription_location(self) -> str:
        return self.transcription_file
