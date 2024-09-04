from threading import Thread
from queue import Queue
from deep_translator import GoogleTranslator
import speech_recognition as sr

r = sr.Recognizer()
audio_queue = Queue()


def speech_recognition():
    # this runs in a background thread
    while True:
        audio = audio_queue.get()  # retrieve the next audio processing job from the main thread
        if audio is None:
            break  # stop processing if the main thread is done

        # received audio data, now we'll recognize it using Google Speech Recognition
        try:
            # for testing purposes, we're just using the default API key
            # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
            # instead of `r.recognize_google(audio)`
            text = r.recognize_whisper(audio)
            print("Decoded Text: {}".format(text))
            print(translate(text=text))

        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print("Request results error")

        audio_queue.task_done()  # mark the audio processing job as completed in the queue


def translate(source='en', target='zh-CN', text=''):
    # https://pypi.org/project/deep-translator/#google-translate-1
    return GoogleTranslator(source=source, target=target).translate(text)


# start a new thread to recognize audio, while this thread focuses on listening
recognize_thread = Thread(target=speech_recognition)
recognize_thread.daemon = True
recognize_thread.start()
with sr.Microphone() as source:
    try:
        print("Adjusting noise...")
        r.adjust_for_ambient_noise(source, duration=1)
        print("Recording...")
        while True:  # repeatedly listen for phrases and put the resulting audio on the audio processing job queue
            audio_queue.put(r.listen(source))
    except KeyboardInterrupt:  # allow Ctrl + C to shut down the program
        print("Interrupted")
        pass

audio_queue.join()  # block until all current audio processing jobs are done
audio_queue.put(None)  # tell the recognize_thread to stop
recognize_thread.join()  # wait for the recognize_thread to actually stop
