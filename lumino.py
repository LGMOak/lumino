import speech_recognition as sr
import os
from deep_translator import GoogleTranslator
from deepl import Translator


class Lumino:
    def __init__(self):
        self.DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
        self.model = 'google'
        # self.model = 'deepl'
        self.recognizer = sr.Recognizer()

    def translate(self, source='en', target='zh-CN', text=''):
        # https://pypi.org/project/deep-translator/#google-translate-1
        return GoogleTranslator(source=source, target=target).translate(text)

    def speech_recog(self):
        # List available microphones (optional)
        print("Available microphones:")
        print(sr.Microphone.list_microphone_names())

        # Select a specific microphone (optional)
        # with sr.Microphone(device_index=1) as source:

        with sr.Microphone() as source:
            print("Adjusting noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Recording for 4 seconds...")
            recorded_audio = self.recognizer.listen(source, timeout=4)
            print("Done recording.")

            try:
                print("Recognizing the text...")
                text = self.recognizer.recognize_whisper(recorded_audio, language="en", model="small")
                print("Decoded Text: {}".format(text))
                return text
            except sr.UnknownValueError:
                return "Could not understand the audio."
            except sr.RequestError:
                return "Request results error"
            except Exception:
                return None


if __name__ == "__main__":
    lum = Lumino()
    txt = lum.speech_recog()
    print(txt)
    print(lum.translate(text=txt))
