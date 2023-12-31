import ffmpeg
import torch

from app.models.MediaFileModel import MediaFileModel
from app.config import WAV_SAMPLING_RATE, MAX_CHUNK_DURATION_S, MIN_CHUNK_DURATION_S


def detect_timestamps(pcm_wav_file) -> list:
    supported_sampling_rates = [8000, 16000]
    if WAV_SAMPLING_RATE not in supported_sampling_rates:
        raise RuntimeError(
            f"Sampling rate {WAV_SAMPLING_RATE} is not supported. "
            f"Supported sampling rates are {supported_sampling_rates}"
        )

    silero_model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad", model="silero_vad", onnx=True
    )
    get_speech_timestamps, _, read_audio, _, _ = utils

    audio = read_audio(pcm_wav_file, sampling_rate=WAV_SAMPLING_RATE)

    silero_timestamps = get_speech_timestamps(
        audio=audio,
        model=silero_model,
        threshold=0.5,
        sampling_rate=WAV_SAMPLING_RATE,
        min_speech_duration_ms=500,
        min_silence_duration_ms=500,
    )

    for timestamps in silero_timestamps:
        timestamps["start"] = float(timestamps["start"] / WAV_SAMPLING_RATE)
        timestamps["end"] = float(timestamps["end"] / WAV_SAMPLING_RATE)

    return silero_timestamps


def calculate_chunks(silero_timestamps: list, audio_duration_s: int) -> list:
    chunks = []
    start = 0.0

    if audio_duration_s <= MAX_CHUNK_DURATION_S:
        return [[start, audio_duration_s]]

    while start < audio_duration_s:
        end = min(start + MAX_CHUNK_DURATION_S, audio_duration_s)
        best_cut_position = find_best_cut_position(
            silero_timestamps, start + MIN_CHUNK_DURATION_S, end
        )
        if best_cut_position and abs(best_cut_position - start) >= MIN_CHUNK_DURATION_S:
            chunks.append([start, best_cut_position])
            start = best_cut_position
        else:
            if end - start < MIN_CHUNK_DURATION_S:
                end = min(start + MIN_CHUNK_DURATION_S, audio_duration_s)
            chunks.append([start, end])
            start = end

    return chunks


def find_best_cut_position(
    silero_timestamps: list, start: float, end: float
) -> float or None:
    longest_silence_position = None
    longest_silence_duration = 0

    for i in range(len(silero_timestamps) - 1):
        silence_start = silero_timestamps[i]["end"]
        silence_end = silero_timestamps[i + 1]["start"]
        silence_duration = silence_end - silence_start
        if (
            silence_start >= start
            and silence_end <= end
            and silence_duration > longest_silence_duration
        ):
            longest_silence_position = silence_start + silence_duration / 2
            longest_silence_duration = silence_duration

    return longest_silence_position


def split_audio_into_chunks(chunks: list, media_file: MediaFileModel):
    input_file = media_file.pcm_wav_file

    for i, chunk in enumerate(chunks):
        output_file_name = media_file.get_chunk_location(i)
        ss = chunk[0]  # start time of the chunk, in seconds
        to = chunk[1]  # end time of the chunk, in seconds
        duration = to - ss

        # split audio at this chunk
        ffmpeg.input(input_file).output(output_file_name, ss=ss, t=duration).run(
            overwrite_output=True
        )
