from app.ChunkProcessor import ChunkProcessor


def test_silero_timestamps():
    audio_file_path = f"test_files/chekhov.wav"

    silero_timestamps = ChunkProcessor.detect_timestamps(audio_file_path)

    assert len(silero_timestamps) > 0

    # Check the first few results
    assert abs(silero_timestamps[0]['start'] - 1.89) / 1.89 < 0.005
    assert abs(silero_timestamps[0]['end'] - 4.062) / 4.062 < 0.005

    assert abs(silero_timestamps[1]['start'] - 4.962) / 4.962 < 0.005
    assert abs(silero_timestamps[1]['end'] - 6.942) / 6.942 < 0.005

    assert abs(silero_timestamps[2]['start'] - 7.746) / 7.746 < 0.005
    assert abs(silero_timestamps[2]['end'] - 8.574) / 8.574 < 0.005
