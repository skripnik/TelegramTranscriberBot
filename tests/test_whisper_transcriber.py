from app.WhisperTranscriber import WhisperTranscriber


def test_transcription():
    audio_file_path = f"test_files/chekhov.mp3"
    transcript = WhisperTranscriber.transcribe_audio(audio_file_path)
    assert transcript.startswith("Антон Павлович Чехов, «Толстый и тонкий». Рассказ")
