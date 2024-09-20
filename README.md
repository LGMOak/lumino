## DECO3801 Lumino
Description here

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

