import os
import time
import datetime
import sys
import os
import torch
import whisper
import numpy as np
import speech_recognition as sr
from queue import Queue


class Lumino:
    def main(self):
        # Time when a spoken line was taken fom queue
        line_time = None

        audio_queue = Queue()

        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = False

        # common linux bug
        source = None
        if 'linux' in sys.platform:
            mic_name = "pulse"
            for i, mic in enumerate(sr.Microphone.list_microphone_names()):
                if mic_name in mic:
                    source = sr.Microphone(sample_rate=16000, device_index=i)
                    break
        else:
            source = sr.Microphone()

        # Load / Download model
        audio_model = whisper.load_model("small")

        # How real time the recording is in seconds.
        record_timeout = 2
        # How much empty space between recordings before we consider it a new line in the transcription.
        line_timeout = 3

        speech_text = ['']

        print("Adjusting noise...")
        with source:
            recognizer.adjust_for_ambient_noise(source, duration=1)

        def recognise(r, audio_data: sr.AudioData):
            """
            Get the audio data line-by-line and add to queue
            :param audio_data: incoming audio stream
            :return:
            """
            data = audio_data.get_raw_data()
            audio_queue.put(data)

        recognizer.listen_in_background(source, recognise, phrase_time_limit=line_timeout)

        # audio data in bytes
        audio_data = b''

        while True:
            try:
                start = time.time()

                if not audio_queue.empty():
                    line_end = False
                    # line ends when 3s has passed
                    if time.time() - start > line_timeout:
                        line_end = True
                        # new audio data -> new line
                        audio_data = b''
                    line_time = start

                    # combine audio data
                    audio_data = audio_data + b''.join(audio_queue.queue)
                    audio_queue.queue.clear()

                    # numpy torch audio data stuff
                    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                    # Read the transcription.
                    result = audio_model.transcribe(audio_np, fp16=torch.cuda.is_available())
                    text = result['text'].strip()

                    # either add new line or edit last line
                    if line_end:
                        speech_text.append(text)
                    else:
                        speech_text[-1] = text

                    os.system('cls' if os.name == 'nt' else 'clear')
                    for line in speech_text:
                        print(line)
                    print('', end='', flush=True)
            except KeyboardInterrupt:
                break


if __name__ == "__main__":
    lum = Lumino()
    lum.main()
