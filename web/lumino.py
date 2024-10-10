import time
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
import threading

class Lumino:
    def __init__(self):
        self.DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
        self.spoken_language = "EN"
        self.target_language = "ZH"
        self.scenarios = {"General": "Translation for Chinese elderly immigrant in Australia. Context is general and informal",
                          "Community": "Translation for Chinese elderly immigrant in Australia. User is interacting out with local community, friends, family or workers",
                          "Medical": "Translation for Chinese elderly immigrant in Australia. User has an appointment with a medical doctor.",
                          "Social": "Translation for Chinese elderly immigrant in Australia. User has an appointment with a social service worker. Centrelink is name of services program"}
        self.selected_scenario = "General"
        self.line_time = None
        self.audio_queue = Queue()
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = False
        gem.configure(api_key=GEMINI_API_KEY)
        self.model = gem.GenerativeModel("gemini-1.5-flash")
        self.source = None
        self.audio_model = whisper.load_model("small")
        self.record_timeout = 2
        self.line_timeout = 3
        self.speech_text = ['']
        self.spoken_line = ""
        self.stop_event = threading.Event()
        self.stop_listening = None

    def translate(self, source='EN', target='ZH-HANS', text=''):
        translator = deepl.Translator(DEEPL_API_KEY)
        formality = 'prefer_less' if self.get_context() not in ["Medical", "Services"] else 'prefer_more'
        return translator.translate_text(text=text, source_lang=source, target_lang=target,
                                         context=self.get_scenarios()[self.get_context()], formality=formality).text

    def set_input_source(self, input_device):
        try:
            self.source = sr.Microphone(input_device, sample_rate=16000)
            print(f"Microphone set to: {self.source}")  # Log the microphone setup
        except Exception as e:
            print(f"Error setting microphone source: {e}")
            self.source = sr.Microphone(sample_rate=16000)

    def set_language(self, speaking_language):
        self.target_language = self.spoken_language
        self.spoken_language = speaking_language

    def generate_context(self, prompt=""):
        context_prompt = (f"Explain this conversation for me so far in as few sentences as possible: {prompt}."
                          f"Try to infer the context of the conversation, where the scenario is {self.get_scenarios()[self.get_context()]}"
                          f" given all the previous lines. Give the entire output in {self.target_language} language")
        response = self.model.generate_content(f"{context_prompt}")
        return response.text

    def get_context(self):
        return self.selected_scenario

    def set_context(self, context_scenario):
        self.selected_scenario = context_scenario

    def get_scenarios(self):
        return self.scenarios

    def reset_stop_event(self):
        self.stop_event.clear()
        self.stop_listening = None

    def stop_recognition(self):
        self.stop_event.set()
        if self.stop_listening is not None:
            self.stop_listening()
            self.stop_listening = None
        self.audio_queue.queue.clear()

    def clear_conversation(self):
        """
        Clear the conversation history for a new session.
        """
        self.speech_text = ['']
        self.spoken_line = ""

    def speech_recognition(self):
        print("Setting up microphone")
        if self.source is None:
            self.source = sr.Microphone(sample_rate=16000)

        with self.source as source:
            try:
                print("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            except Exception as e:
                print(f"Error adjusting for ambient noise: {e}")
                return

        def transcript_data(r, audio_data: sr.AudioData):
            data = audio_data.get_raw_data()
            self.audio_queue.put(data)

        print("Recording...")
        # save the stop function
        self.stop_listening = self.recognizer.listen_in_background(self.source, transcript_data, phrase_time_limit=self.record_timeout)
        audio_data = b''

        while not self.stop_event.is_set():
            try:
                if not self.audio_queue.empty():
                    audio_data = b''.join(list(self.audio_queue.queue))
                    self.audio_queue.queue.clear()
                    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                    result = self.audio_model.transcribe(audio_np, fp16=torch.cuda.is_available())
                    text = result['text'].strip()
                    if self.speech_text[-1] == "":
                        self.speech_text[-1] = text
                    else:
                        self.speech_text[-1] += f" {text}"
                    self.spoken_line = self.speech_text[-1]
                    if self.spoken_language == "ZH":
                        translation = self.translate(source='ZH', target='EN-GB', text=self.spoken_line)
                    else:
                        translation = self.translate(text=self.spoken_line)
                    context = self.generate_context(self.spoken_line)
                    yield self.spoken_line, translation, context

                     # Print recognized and translated text to the console
                    print(f"Recognized Text: {text}")
                    print(f"Translated Text: {translation}")
                    yield self.spoken_line, translation, context

            except KeyboardInterrupt:
                return self.speech_text, None, None
            except Exception as e:
                print(f"Error during recognition: {e}")
        print("Speech recognition stopped.")
