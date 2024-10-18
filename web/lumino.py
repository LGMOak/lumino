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
    """
    The Lumino class manages speech recognition, translation, and context generation.
    This class includes microphone initialization, audio processing, translation functionality, and generating conversation context.
    """

    def __init__(self):
        """
        Initialize an instance of the Lumino class, including setting language, context, microphone source, and speech recognition model.
        """
        self.DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")  # Get Deepl API key
        self.spoken_language = "EN"  # Default spoken language
        self.target_language = "ZH"  # Default target language
        # Scenarios and their descriptions used to generate context
        self.scenarios = {
            "General 通用": "This context refers to everyday, general conversations without specific focus that an elderly Chinese immigrant in Australia may have. It covers casual interactions that are not tied to any particular domain, such as greetings, basic questions, or social small talk. In this context, the conversation could involve a variety of topics ranging from weather, personal well-being, or simple inquiries. The goal is to keep the translation as neutral and everyday as possible, avoiding any specialized terminology.",
            "Local Community 社区": "This context relates to conversations within the local community, such as interactions with family members, friends, neighbors, tradespeople, shop owners, cashiers, and other people you encounter regularly in your day-to-day life. This includes small transactions, informal exchanges, asking for help, or engaging with people in familiar settings. The language used here is more informal, reflecting the tone of a community that is close-knit and casual.",
            "Social Services 社会服务": "This context involves conversations related to government services and welfare programs in Australia, such as Centrelink (financial assistance), Medicare (public healthcare), superannuation (retirement savings), pensions, taxes, and other services that assist in everyday living. It includes discussions about applying for benefits, understanding rights and entitlements, navigating bureaucracy, and engaging with service providers. The language should be clear, straightforward, and possibly include formal or legal terminology often used in public services.",
            "Medical Services 医疗": "This context focuses on medical-related conversations, including interactions with healthcare professionals like general practitioners (GPs), hospitals, physiotherapists, pharmacists, and nurses. It covers discussions about appointments, medical treatments, prescriptions, health advice, and explanations of medical conditions. In this context, the language is both technical (with medical terminology) and conversational, reflecting the seriousness of healthcare while remaining accessible for patients, especially those unfamiliar with medical terms. Understanding the correct use of terminology is key to avoid confusion."
        }
        self.selected_scenario = "General 通用"  # Default scenario
        self.line_time = None
        self.audio_queue = Queue()  # Queue for storing audio data
        self.recognizer = sr.Recognizer()  # Initialize speech recognizer
        self.recognizer.dynamic_energy_threshold = False  # Disable dynamic energy threshold
        gem.configure(api_key=GEMINI_API_KEY)  # Configure generative AI API key
        self.model = gem.GenerativeModel("gemini-1.5-flash")  # Initialize generative AI model
        self.source = None  # Microphone source
        self.audio_model = whisper.load_model("small")  # Load Whisper speech recognition model
        self.record_timeout = 2  # Recording timeout
        self.line_timeout = 3  # Line timeout
        self.speech_text = ['']  # Store the entire conversation text
        self.spoken_line = ""  # Current spoken line
        self.stop_event = threading.Event()  # Event to stop speech recognition
        self.stop_listening = None  # Save the stop listening function

    def translate(self, source='EN', target='ZH-HANS', text=''):
        """
        Translate text using Deepl API.
        
        Args:
            source (str): Source language code.
            target (str): Target language code.
            text (str): Text to be translated.
        
        Returns:
            str: Translated text.
        """
        translator = deepl.Translator(DEEPL_API_KEY)
        formality = 'prefer_less' if self.get_context() not in ["Medical Services 医疗", "Social Services 社会服务"] else 'prefer_more'
        return translator.translate_text(text=text, source_lang=source, target_lang=target,
                                         context=self.get_scenarios()[self.get_context()], formality=formality).text

    def set_input_source(self, input_device):
        """
        Set the input audio source (microphone).
        
        Args:
            input_device (int): Index of the input device.
        """
        try:
            self.source = sr.Microphone(input_device, sample_rate=16000)
            print(f"Microphone set to: {self.source}")  # Log microphone setup information
        except Exception as e:
            print(f"Error setting microphone source: {e}")
            self.source = sr.Microphone(sample_rate=16000)  # Set default microphone

    def set_language(self, speaking_language):
        """
        Set the spoken and target languages.
        
        Args:
            speaking_language (str): Spoken language.
        """
        self.target_language = self.spoken_language
        self.spoken_language = speaking_language

    def generate_context(self, prompt=""):
        """
        Generate conversation context based on the current scenario and previous conversation.
        
        Args:
            prompt (str): Current conversation text.
        
        Returns:
            str: Generated context text.
        """
        context_prompt = (f"Explain this conversation for me so far in as few sentences as possible: {prompt}."
                          f"Try to infer the context of the conversation, where the scenario is {self.get_scenarios()[self.get_context()]}"
                          f" given all the previous lines. Give the entire output in {self.target_language} language")
        response = self.model.generate_content(f"{context_prompt}")
        return response.text

    def get_context(self):
        """
        Get the current conversation scenario.
        
        Returns:
            str: The currently selected scenario.
        """
        return self.selected_scenario

    def set_context(self, context_scenario):
        """
        Set the conversation scenario.
        
        Args:
            context_scenario (str): Selected scenario.
        """
        self.selected_scenario = context_scenario

    def get_scenarios(self):
        """
        Get all available scenarios.
        
        Returns:
            dict: All available scenarios and their descriptions.
        """
        return self.scenarios

    def reset_stop_event(self):
        """
        Reset the stop event.
        """
        self.stop_event.clear()
        self.stop_listening = None

    def stop_recognition(self):
        """
        Stop the speech recognition process and clear the audio queue.
        """
        self.stop_event.set()
        if self.stop_listening is not None:
            self.stop_listening()
            self.stop_listening = None
        self.audio_queue.queue.clear()

    def clear_conversation(self):
        """
        Clear the current conversation history for a new session.
        """
        self.speech_text = ['']
        self.spoken_line = ""

    def speech_recognition(self):
        """
        Perform speech recognition, generate recognized text and translated content.
        
        Yields:
            tuple: Contains recognized text, translated text, and generated context.
        """
        print("Setting up microphone")
        if self.source is None:
            self.source = sr.Microphone(14, sample_rate=16000)

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
        # Save the stop function
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

                    # Print recognized and translated text to the console
                    print(f"Recognized Text: {text}")
                    print(f"Translated Text: {translation}")
                    yield self.spoken_line, translation, context

            except KeyboardInterrupt:
                return self.speech_text, None, None
            except Exception as e:
                print(f"Error during recognition: {e}")
        print("Speech recognition stopped.")


if __name__ == '__main__':
    lumino = Lumino()
    for text, translation, context in lumino.speech_recognition():
        print(text, translation, context)