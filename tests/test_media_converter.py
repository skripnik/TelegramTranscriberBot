from app.MediaConverter import MediaConverter


def test_wav_conversion():
    mp3_file_path = f"test_files/chekhov.mp3"
    vaw_file_path = f"test_files/chekhov.wav"

    MediaConverter.convert_to_pcm_wav(mp3_file_path, vaw_file_path)


def test_mp3_conversion():
    ogg_file_path = f"test_files/informburo.ogg"
    mp3_file_path = f"test_files/informburo.mp3"

    MediaConverter.convert_to_mp3(ogg_file_path, mp3_file_path)
