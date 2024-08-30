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

    def __googletranslate(self, source='auto', target='zh-CN', text=''):
        # https://pypi.org/project/deep-translator/#google-translate-1
        return GoogleTranslator(source=source, target=target).translate(text)

    def __deeptranslate(self, source=None, target='en-us', text='', context=None, split_sentences=0,
                        preserve_formatting=False, formality='prefer_less', glossary_id=None):
        # https://developers.deepl.com/docs/api-reference/translate
        # possible glossary implementation
        if self.DEEPL_API_KEY is not None:
            translator = Translator(auth_key=self.DEEPL_API_KEY)
        else:
            raise ValueError(
                f"No API key set. \n Please set your DeepL API key in your "
                f"environment config as the 'DEEPL_API_KEY' variable")

        return translator.translate_text(source_lang=source,
                                         target_lang=target,
                                         text=text,
                                         context=context,
                                         split_sentences=split_sentences,
                                         preserve_formatting=preserve_formatting,
                                         formality=formality).text

    def translate(self, source='auto', target='zh-CN', text='', context=None, split_sentences=0,
                  preserve_formatting=False, formality='prefer_less', glossary_id=None):
        if self.model == 'google':
            return self.__googletranslate(source=source, target=target, text=text)
        elif self.model == 'deepl':
            return self.__deeptranslate(source=source, target=target, text=text, context=context,
                                        split_sentences=split_sentences, preserve_formatting=preserve_formatting,
                                        formality=formality, glossary_id=glossary_id)
        else:
            print(f'Choose a valid model')

    def speech_recog(self):
        try:
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
                    return self.translate(source='en', target='zh-CN', text=text)
                except sr.UnknownValueError:
                    return "Could not understand the audio."
                except sr.RequestError:
                    return "Request results error"
                except Exception as ex:
                    return "Error during recognition:", ex
        except:
            err = "An error has occurred"
            return err


if __name__ == "__main__":
    lum = Lumino()
    print(lum.speech_recog())
