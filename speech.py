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

    def __init__(self):
        # Time when a spoken line was taken fom queue
        self.line_time = None

        self.audio_queue = Queue()

        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = False

        # common linux bug
        self.source = None
        if 'linux' in sys.platform:
            mic_name = "pulse"
            for i, mic in enumerate(sr.Microphone.list_microphone_names()):
                if mic_name in mic:
                    self.source = sr.Microphone(sample_rate=16000, device_index=i)
                    break
        else:
            self.source = sr.Microphone()

        # Load / Download model
        self.audio_model = whisper.load_model("small")

        # How real time the recording is in seconds.
        self.record_timeout = 2
        # How much empty space between recordings before we consider it a new line in the transcription.
        self.line_timeout = 3

        self.speech_text = ['']

        print("Adjusting noise...")
        with self.source:
            self.recognizer.adjust_for_ambient_noise(self.source, duration=1)

    def speech(self):
        def speech_data(r, audio_data: sr.AudioData):
            """
            Get the audio data line-by-line and add to queue
            :param audio_data: incoming audio stream
            :return:
            """
            data = audio_data.get_raw_data()
            self.audio_queue.put(data)

        self.recognizer.listen_in_background(self.source, speech_data, phrase_time_limit=self.line_timeout)

        # audio data in bytes
        audio_data = b''

        while True:
            try:
                start = time.time()

                if not self.audio_queue.empty():
                    line_end = False
                    # line ends when 3s has passed
                    if time.time() - start > self.line_timeout:
                        line_end = True
                        # new audio data -> new line
                        audio_data = b''
                    line_time = start

                    # combine audio data
                    audio_data = audio_data + b''.join(self.audio_queue.queue)
                    self.audio_queue.queue.clear()

                    # numpy torch audio data stuff
                    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                    # Read the transcription.
                    result = self.audio_model.transcribe(audio_np, fp16=torch.cuda.is_available())
                    text = result['text'].strip()

                    # either add new line or edit last line
                    if line_end:
                        self.speech_text.append(text)
                    else:
                        self.speech_text[-1] = text

                    os.system('clear' if os.name == 'posix' else 'cls')
                    yield text
                    # for line in self.speech_text:
                    #     print(line)
                    # print('', end='', flush=True)
            except KeyboardInterrupt:
                return self.speech_text


if __name__ == "__main__":
    l = Lumino()
    for line in l.speech():
        print(line)

