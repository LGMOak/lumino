import speech_recognition as sr
import os

recognizer = sr.Recognizer()

try:
    # List available microphones (optional)
    print("Available microphones:")
    print(sr.Microphone.list_microphone_names())

    # Select a specific microphone (optional)
    # with sr.Microphone(device_index=1) as source:

    with sr.Microphone() as source:
        print("Adjusting noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Recording for 4 seconds...")
        recorded_audio = recognizer.listen(source, timeout=4)
        print("Done recording.")

        try:
            print("Recognizing the text...")
            text = recognizer.recognize_whisper(recorded_audio, language="en", model="small")
            print("Decoded Text: {}".format(text))
        except sr.UnknownValueError:
            print("Could not understand the audio.")
        except sr.RequestError:
            print("Request results error")
        except Exception as ex:
            print("Error during recognition:", ex)
finally:
    pass