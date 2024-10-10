## DECO3801 Lumino
lumino.py holds all the functionality and can be run on its own for testing.
app.py is the main file that hosts the flask website and connects all functionality.
speech.py, translate.py and generate.py are all standalone programs for speech recognition / transcription, text translation and AI context generation respectively. These are simple examples for testing and can each be run on their own.
Requires an API key to generative LLM. Google's Gemini currently implemented. Support for OpenAI and Antrhoptic. 
Translation using DeepL requires API key. Google Translate does not require API key

## Library Requirements
```python
pip install -r requirements.txt
```

Lumino makes use of:
- SpeechRecognition
- pyaudio
- Flask
- flask-socketio
- setuptools
- pyaudio
- deep_translator
- deepl
- numpy
- openai_whisper
- torch 
- google-generativeai

If issues occur, remove the strict version requirement in requirements.txt and install the latest version of each package

## Installation instructions
Python v3.12.x is recommended version of python. It is also highly recommended to create a new venv to run this application
```
python3 -m venv <venvname>
source <venvname>/bin/activate
```

For microphone recognition, pyaudio must be installed. This is highly dependent on OS.
- On windows
  - `pip install pyaudio`
- On OSX
  - `brew install portaudio` followed by `pip install pyaudio`
- On Linux, pulseaudio is highly recommended
  - `sudo apt-get install pulseaudio`   
  - `sudo apt-get install portaudio19-dev python-all-dev python3-all-dev && sudo pip3 install pyaudio`
 
Furthermore, the available and selected microphones are highly device dependent so some modifications may be required.
```python
import speech_recognition as sr

sr.Microphone.list_working_microphones()
sr.Microphone.list_microphone_names()
```
This gives a list of which microphones are active and the position of all microphones. 
Line 38 of Lumino.py may need to be adapted to 
```python
self.source = sr.Microphone(i)
```
where `i` is the index position of desired microphone. Typically, `self.source = sr.Microphone()` should suffice, but this is not guaranteed. 

