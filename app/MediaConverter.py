import ffmpeg

from config import WAV_SAMPLING_RATE


class MediaConverter:

    @staticmethod
    def convert_to_mp3(input_file_location: str, output_file_location: str) -> None:
        try:
            input_file = ffmpeg.input(input_file_location)
            output_file = input_file.output(
                output_file_location,
                format='mp3',
                acodec='libmp3lame',
                ac=1,
                ar='24000',
                ab='64k',
                map_metadata='-1'
            )
            output_file.run(overwrite_output=True)
        except ffmpeg.Error as e:
            print(f'Error occurred during conversion: {e.stderr.decode()}')
            raise e

    @staticmethod
    def convert_to_pcm_wav(input_file_location: str, output_file_location: str) -> None:
        try:
            input_file = ffmpeg.input(input_file_location)
            output_file = input_file.output(
                output_file_location, format='wav',
                acodec='pcm_s16le',
                ar=WAV_SAMPLING_RATE)
            output_file.run(overwrite_output=True)
        except ffmpeg.Error as e:
            print(f'Error occurred during conversion: {e.stderr.decode()}')
            raise e
