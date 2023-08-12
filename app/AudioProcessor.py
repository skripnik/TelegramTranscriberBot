import os
import ffmpeg
import torch

from config import DATA_DIR


class AudioProcessor:
    WAV_SAMPLING_RATE = 16000
    MIN_CHUNK_DURATION_S = 1 * 60
    MAX_CHUNK_DURATION_S = 4 * 60

    def __init__(self, input_file, file_id):
        self.input_file = input_file
        self.file_id = file_id
        self.audio_dir = f"{DATA_DIR}/converted_files/{self.file_id}"
        self.wav_file = f"{self.audio_dir}/whole.wav"
        self.mp3_file = f"{self.audio_dir}/whole.mp3"
        self.file_duration = None
        self.silero_timestamps = None
        self.chunks = None
        self.audacity_speech_labels = f"{self.audio_dir}/audacity_speech.txt"
        self.audacity_chunk_labels = f"{self.audio_dir}/audacity_chunks.txt"

        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)

    def convert_to_mp3(self):
        try:
            input_file = ffmpeg.input(self.input_file)
            output_file = input_file.output(self.mp3_file, format='mp3')
            output_file.run(overwrite_output=True)

            return output_file
        except ffmpeg.Error as e:
            print(f'Error occurred during conversion: {e.stderr.decode()}')
            raise e

    def convert_to_wav(self):
        try:
            input_file = ffmpeg.input(self.input_file)
            output_file = input_file.output(
                self.wav_file, format='wav',
                acodec='pcm_s16le',
                ar=self.WAV_SAMPLING_RATE)
            output_file.run(overwrite_output=True)

            return output_file
        except ffmpeg.Error as e:
            print(f'Error occurred during conversion: {e.stderr.decode()}')
            raise e

    def detect_chapters(self):
        silero_model, utils = (torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            onnx=True
        ))
        get_speech_timestamps, _, read_audio, _, _ = utils

        audio = read_audio(self.wav_file, sampling_rate=self.WAV_SAMPLING_RATE)

        silero_timestamps = get_speech_timestamps(
            audio=audio,
            model=silero_model,
            threshold=0.5,
            sampling_rate=self.WAV_SAMPLING_RATE,
            min_speech_duration_ms=500,
            min_silence_duration_ms=500
        )

        for timestamps in silero_timestamps:
            timestamps['start'] = float(timestamps['start'] / self.WAV_SAMPLING_RATE)
            timestamps['end'] = float(timestamps['end'] / self.WAV_SAMPLING_RATE)

        self.silero_timestamps = silero_timestamps

    def generate_audacity_speech_labels(self):
        formatted_lines = []

        for timestamps in self.silero_timestamps:
            start_time = format(timestamps['start'], '.3f')
            end_time = format(timestamps['end'], '.3f')
            label = "speech"
            formatted_line = f"{start_time}\t{end_time}\t{label}"
            formatted_lines.append(formatted_line)

        with open(self.audacity_speech_labels, "w") as f:
            f.write("\n".join(formatted_lines))

    def generate_audacity_chunk_labels(self):
        chunks = []

        audio_len_s = self.silero_timestamps[-1]['end']

        if audio_len_s <= self.MAX_CHUNK_DURATION_S:
            chunks.append([0, audio_len_s])
        else:
            start = 0.0
            while start < audio_len_s:
                end = min(start + self.MAX_CHUNK_DURATION_S, audio_len_s)
                silence_interval = self.find_longest_silence_interval(start + self.MIN_CHUNK_DURATION_S, end)
                if silence_interval and abs(silence_interval[0] - start) >= self.MIN_CHUNK_DURATION_S:
                    cut_point = (silence_interval[0] + silence_interval[1]) / 2  # cut in the middle of silence interval
                    chunks.append([start, cut_point])
                    start = cut_point
                else:
                    if end - start < self.MIN_CHUNK_DURATION_S:
                        end = min(start + self.MIN_CHUNK_DURATION_S, audio_len_s)
                    chunks.append([start, end])
                    start = end

        with open(self.audacity_chunk_labels, "w") as f:
            for chunk in chunks:
                start_time = format(chunk[0], '.3f')
                end_time = format(chunk[1], '.3f')
                label = "chunk"
                formatted_line = f"{start_time}\t{end_time}\t{label}"
                f.write(formatted_line + "\n")

        self.chunks = chunks

    def find_longest_silence_interval(self, start: float, end: float) -> [float, float] or None:
        longest_silence_start = None
        longest_silence_end = None
        longest_silence_duration = 0

        for i in range(len(self.silero_timestamps) - 1):
            if self.silero_timestamps[i]['end'] >= start and self.silero_timestamps[i + 1]['start'] <= end:
                silence_duration = self.silero_timestamps[i + 1]['start'] - self.silero_timestamps[i]['end']
                if silence_duration > longest_silence_duration:
                    longest_silence_start = self.silero_timestamps[i]['end']
                    longest_silence_end = self.silero_timestamps[i + 1]['start']
                    longest_silence_duration = silence_duration

        return [longest_silence_start, longest_silence_end] if longest_silence_duration > 0 else None

    def split_audio_into_chunks(self):
        if self.chunks is None:
            print("Error: No chunks detected. Call 'generate_audacity_chunk_labels' method first.")
            return

        for i, chunk in enumerate(self.chunks):
            output_file_name = f"{self.audio_dir}/chunk_{i}.mp3"
            ss = chunk[0]  # start time of the chunk, in seconds
            to = chunk[1]  # end time of the chunk, in seconds
            duration = to - ss

            try:
                # split audio at this chunk
                ffmpeg.input(self.input_file).output(
                    output_file_name,
                    ss=ss,
                    t=duration,
                    c='copy'
                ).run(overwrite_output=True)

                print(f"Chunk {i} has been created and saved as {output_file_name}")
            except ffmpeg.Error as e:
                print(f"Error occurred during splitting the audio file: {e.stderr.decode()}")
                continue
