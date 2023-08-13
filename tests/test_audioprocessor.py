from app.AudioProcessor import ChunkProcessor


def test_process_audio():
    audio_file_path = f"test_files/chekhov.mp3"

    audioprocessor = ChunkProcessor(audio_file_path, "test")
    audioprocessor.convert_to_wav()
    audioprocessor.detect_timestamps()
    audioprocessor.format_speech_labels_for_audacity()
    audioprocessor.calculate_chunks()
    audioprocessor.split_audio_into_chunks()

    return
