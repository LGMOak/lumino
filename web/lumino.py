import time
import sys
import os
import torch
import whisper
import numpy as np
import speech_recognition as sr
from queue import Queue
import deepl
import google.generativeai as gem
from deep_translator import GoogleTranslator

from keys import GEMINI_API_KEY, DEEPL_API_KEY
import threading  # NEW: Imported threading module to handle stop events


class Lumino:
    def __init__(self):
        self.DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

        self.spoken_language = "EN"

        self.scenarios = {
            "General": "Translation for Chinese elderly immigrant in Australia. Context is general and informal",
            "Community": "Translation for Chinese elderly immigrant in Australia. User is interacting out with local community, friends, family or workers",
            "Medical": "Translation for Chinese elderly immigrant in Australia. User has an appointment with a medical doctor.",
            "Social": "Translation for Chinese elderly immigrant in Australia. User has an appointment with a social service worker. Centrelink is name of services program"}
        self.selected_scenario = "General"

        # Time when a spoken line was taken from queue
        self.line_time = None

        self.audio_queue = Queue()

        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = False

        # LLM for generating user context
        gem.configure(api_key=GEMINI_API_KEY)
        self.model = gem.GenerativeModel("gemini-1.5-flash")

        # default mic
        self.source = None

        # Load / Download model
        self.audio_model = whisper.load_model("small")

        # How real time the recording is in seconds.
        self.record_timeout = 2
        # How much empty space between recordings before we consider it a new line in the transcription.
        self.line_timeout = 3

        # Keep a record of the whole conversation (for context parsing)
        self.speech_text = ['']

        # Spoken line
        self.spoken_line = ""

        # A stop event to stop the recognition
        self.stop_event = threading.Event()  # NEW: Event to signal when to stop recognition

        # Save the stop function from listen_in_background
        self.stop_listening = None  # NEW: Holds the function to stop background listening

    def translate(self, source='EN', target='ZH-HANS', text=''):
        translator = deepl.Translator(DEEPL_API_KEY)

        formality = 'prefer_less'
        if self.get_context() == "Medical" or self.get_context() == "Services":
            formality = 'prefer_more'

        translation = translator.translate_text(text=text, source_lang=source, target_lang=target,
                                                context=self.get_scenarios()[self.get_context()], formality=formality)
        # translation = GoogleTranslator(source='en', target='zh-CN').translate(text)
        return translation

    def set_input_source(self, input_device):

        mic = sr.Microphone(input_device, sample_rate=16000)
        self.source = mic

    def set_language(self, speaking_language):

        self.spoken_language = speaking_language

    def generate_context(self, prompt=""):
        context_prompt = (f"Explain this line in a conversation for me in simple words, "
                          f"given the previous lines. {prompt}")

        response = self.model.generate_content(f"{context_prompt} {prompt}")

        return response.text

    def get_context(self):

        return self.selected_scenario

    def set_context(self, context_scenario):

        self.selected_scenario = context_scenario

    def get_scenarios(self):

        return self.scenarios

    def reset_stop_event(self):
        self.stop_event.clear()
        self.stop_listening = None  # NEW: Reset the stop_listening function

    def stop_recognition(self):
        self.stop_event.set()
        if self.stop_listening is not None:
            self.stop_listening()  # NEW: Stop the background listening
            self.stop_listening = None
        # empty the queue
        self.audio_queue.queue.clear()  # NEW: Clear the audio queue

    def speech_recognition(self):
        print("Setting up microphone")
        print(self.source)
        if self.source is None:
            self.source = sr.Microphone(14, sample_rate=16000)

        print("Adjusting noise...")
        print(self.source)
        with self.source as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

        def transcript_data(r, audio_data: sr.AudioData):
            data = audio_data.get_raw_data()
            self.audio_queue.put(data)

        print("Recording...")
        # save the stop function
        self.stop_listening = self.recognizer.listen_in_background(
            self.source, transcript_data, phrase_time_limit=self.record_timeout)  # NEW: Save the stop function

        # audio data in bytes
        audio_data = b''

        while not self.stop_event.is_set():  # NEW: Check the stop event
            try:
                start = time.time()

                if not self.audio_queue.empty():
                    line_end = False
                    # Line ends when 3s has passed
                    if time.time() - start > self.line_timeout:
                        line_end = True
                        # New audio data -> new line
                        audio_data = b''
                    self.line_time = start

                    # Combine audio data
                    audio_data = audio_data + b''.join(self.audio_queue.queue)
                    self.audio_queue.queue.clear()

                    # Numpy torch audio data stuff
                    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                    # Read the transcription.
                    result = self.audio_model.transcribe(audio_np, fp16=torch.cuda.is_available())
                    text = result['text'].strip()

                    # Either add new line or edit last line
                    if line_end:
                        # Append to whole speech
                        self.speech_text.append(text)
                    else:
                        # Edit line
                        self.speech_text[-1] = text

                    # Record newest line separately from whole conversation
                    self.spoken_line = text

                    if self.spoken_language == "ZH":
                        translation = self.translate(source='ZH', target='EN-GB', text=text)
                    else:
                        translation = self.translate(text=text)

                    # Generate context
                    context = self.generate_context(self.spoken_line)
                    yield self.spoken_line, translation, context

            except KeyboardInterrupt:
                return self.speech_text, None, None
        print("Speech recognition stopped.")  # NEW: Indicate that recognition has stopped


if __name__ == "__main__":
    l = Lumino()
    for line, translated, context in l.speech_recognition():
        print("Recognised: ", line)
        print(f"Translated: {translated}")
        print(f"Context: {context}")
