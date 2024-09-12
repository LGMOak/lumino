import speech_recognition as sr
import os
from queue import Queue
from threading import Thread
from deep_translator import GoogleTranslator
from deepl import Translator


class Lumino:
    def __init__(self):
        self.DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
        self.model = 'google'
        # self.model = 'deepl'
        self.recognizer = sr.Recognizer()

        # queue for audio stream; list for text result
        self.audio_queue = Queue()
        self.speech_text = []

    def speech_to_text(self):
        # start a new thread to recognize audio, while this thread focuses on listening
        recognize_thread = Thread(target=self.__speech_recog)
        recognize_thread.daemon = True
        recognize_thread.start()

        with sr.Microphone() as source:
            try:
                print("Adjusting noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("Recording...")
                while True:  # repeatedly listen for phrases and put the resulting audio on the audio processing job queue
                    self.audio_queue.put(self.recognizer.listen(source))
            except KeyboardInterrupt:  # allow Ctrl + C to shut down the program
                print("\nInterrupted")
                # print(self.speech_text)
                return self.speech_text

    def translate(self, source='en', target='zh-CN', text=''):
        # https://pypi.org/project/deep-translator/#google-translate-1
        return GoogleTranslator(source=source, target=target).translate(text)

    def __speech_recog(self):
        # this runs in a background thread
        while True:
            audio = self.audio_queue.get()  # retrieve the next audio processing job from the main thread
            if audio is None:
                break  # stop processing if the main thread is done

            # received audio data, now we'll recognize it using Google Speech Recognition
            try:
                # for testing purposes, we're just using the default API key
                # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
                # instead of `r.recognize_google(audio)`
                text = self.recognizer.recognize_whisper(audio)
                print(text)
                self.speech_text.append(text)
                # print(self.translate(text=text))

            except sr.UnknownValueError as uve:
                self.speech_text.append(uve)
            except sr.RequestError as e:
                return self.speech_text.append(e)
            finally:
                self.audio_queue.task_done()  # mark the audio processing job as completed in the queue


if __name__ == "__main__":
    lum = Lumino()
    txt = ''.join(lum.speech_to_text())
    print(txt)
    print(lum.translate(text=txt))