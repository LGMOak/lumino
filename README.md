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
It is highly recommended to create a new venv to run this application
```
python3 -m venv <venvname>
source <venvname>/bin/activate
```

For microphone recognition, pyaudio must be installed. This is highly dependent on OS.
- On windows
  - `pip install pyaudio`
- On OSX
  - `brew install portaudio` followed by `pip install pyaudio`
- On Linux
  - `sudo apt-get install portaudio19-dev python-all-dev python3-all-dev && sudo pip3 install pyaudio`  
