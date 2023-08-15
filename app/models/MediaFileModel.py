import os
import json
from jinja2 import Environment, FileSystemLoader


class MediaFileModel:
    def __init__(self, user_id, message_id, data_dir: str):
        self.folder = f"{data_dir}/{user_id}/{message_id}"
        self.original_file_id = None
        self.original_file_type = None
        self.original_file_duration_s = None
        self.original_file_location = None
        self.original_file_extension = None
        self.pcm_wav_file = f"{self.folder}/converted.wav"
        self.mp3_file = f"{self.folder}/converted.mp3"
        self.audacity_speech_labels = f"{self.folder}/audacity_speech.txt"
        self.audacity_chunk_labels = f"{self.folder}/audacity_chunks.txt"
        self.silero_timestamps_json = f"{self.folder}/silero_timestamps.json"
        self.transcription_file = f"{self.folder}/transcription.html"

    def save_user_media(self, file_contents: bytearray):
        self.original_file_location = f"{self.folder}/original"

        if self.original_file_extension:
            self.original_file_location = f"{self.original_file_location}.{self.original_file_extension}"

        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

        with open(self.original_file_location, "wb") as file:
            file.write(file_contents)

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

    def save_transcription(self, paragraphs: list):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        view_path = os.path.join(dir_path, '..', 'views')
        env = Environment(loader=FileSystemLoader(view_path))
        template = env.get_template('transcription_template.html')

        rendered_template = template.render(paragraphs=paragraphs)

        with open(self.transcription_file, "w") as file:
            file.write(rendered_template)
