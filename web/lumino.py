import time
import sys
import os
import torch
import whisper
import numpy as np
import speech_recognition as sr
from queue import Queue
from deep_translator import GoogleTranslator
import google.generativeai as gem
from keys import GEMINI_API_KEY


class Lumino:
    def __init__(self):
        self.DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

        self.spoken_language = "EN"

        self.scenario = "Centrelink"

        # Time when a spoken line was taken fom queue
        self.line_time = None

        self.audio_queue = Queue()

        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = False

        # LLM for generating user context
        gem.configure(api_key=GEMINI_API_KEY)
        self.model = gem.GenerativeModel("gemini-1.5-flash")

        # default mic
        self.source = sr.Microphone(sample_rate=16000)

        # Load / Download model
        self.audio_model = whisper.load_model("small")

        # How real time the recording is in seconds.
        self.record_timeout = 2
        # How much empty space between recordings before we consider it a new line in the transcription.
        self.line_timeout = 3

        # keep a record of the whole conversation (for context parsing)
        self.speech_text = ['']

        # spoken line
        self.spoken_line = ""

    def translate(self, source='en', target='zh-CN', text=''):
        # https://pypi.org/project/deep-translator/#google-translate-1
        translation = GoogleTranslator(source=source, target=target).translate(text)
        # translation = Translator(auth_key=self.DEEPL_API_KEY).translate_text(source_lang='EN-US', target_lang='ZH-HANS',
        #                                                                      text=text, context="Medical checkup appointment")
        return translation

    def set_input_source(self, input_device):
        print(input_device)
        self.source = sr.Microphone(sample_rate=16000, device_index=int(input_device))

    def set_language(self, speaking_language):
        print(speaking_language)
        self.spoken_language = speaking_language

    def set_context(self, context_scenario):
        print(context_scenario)
        self.scenario = context_scenario

    def generate_context(self, prompt=""):
        context_prompt = (f"Explain this line in a conversation for me in simple words, "
                          f"given the previous lines. {prompt}")

        response = self.model.generate_content(f"{context_prompt} {prompt}")

        return response.text
    def speech_recognition(self):
        print("Adjusting noise...")
        print(self.source)
        with self.source:
            self.recognizer.adjust_for_ambient_noise(self.source, duration=1)
        def transcript_data(r, audio_data: sr.AudioData):
            """
            Get the audio data line-by-line and add to queue
            :param audio_data: incoming audio stream
            :return:
            """
            data = audio_data.get_raw_data()
            self.audio_queue.put(data)

        print("Recording...")
        self.recognizer.listen_in_background(self.source, transcript_data, phrase_time_limit=self.record_timeout)

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
                    self.line_time = start

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
                        # append to whole speech
                        self.speech_text.append(text)
                    else:
                        # Edit line
                        self.speech_text[-1] = text

                    # record newest line separately from whole conversation
                    self.spoken_line = text

                    print(self.spoken_language, text)
                    if self.spoken_language == "ZH":
                        translation = self.translate(source='zh-CN', target='en', text=text)
                    else:
                        translation = self.translate(text=text)

                    # conversation = ' '.join(self.speech_text)
                    context = self.generate_context(self.spoken_line)
                    yield self.spoken_line, translation, context

            except KeyboardInterrupt:
                return self.speech_text, None, None


if __name__ == "__main__":
    l = Lumino()
    for line, translated, context in l.speech_recognition():
        print("Recognised: ", line)
        print(f"Translated: {translated}")
        print(f"Context: {context}")

