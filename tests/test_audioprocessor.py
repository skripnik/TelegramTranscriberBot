from app.AudioProcessor import AudioProcessor


def test_process_audio():
    audio_file_path = f"test_files/chekhov.mp3"

    audioprocessor = AudioProcessor(audio_file_path, "test")
    audioprocessor.convert_to_wav()
    audioprocessor.detect_chapters()
    audioprocessor.generate_audacity_speech_labels()
    audioprocessor.generate_audacity_chunk_labels()
    audioprocessor.split_audio_into_chunks()

    return
