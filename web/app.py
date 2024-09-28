from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from lumino import Lumino
from threading import Thread, Event
import speech_recognition as sr

# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'  # Set the secret key for session management
socketio = SocketIO(app)  # Wrap the app with SocketIO to enable WebSocket support

# Global variables to manage the Lumino instance and threading
lumino_instance = Lumino()        # Holds the instance of the Lumino class
recognition_thread = None     # The background thread that runs speech recognition
thread_stop_event = None      # Event to signal the thread to stop
audio_sources = sr.Microphone.list_microphone_names()

@app.route('/')
def index():
    """
    Handle the root URL and render the main page.
    """
    language = request.args.get('lang', 'EN')
    if language is not None:
        lumino_instance.set_language(language)

    selected_mic = request.args.get('microphone', 0)
    if selected_mic is not None and selected_mic != '':
        lumino_instance.set_input_source(selected_mic)

    selected_context = request.args.get('selected_option', 'General')
    if selected_context is not None:
        lumino_instance.set_context(selected_context)

    return render_template('index.html', language=lumino_instance.spoken_language, mics=audio_sources,
                           selected_mic=selected_mic, mic_name=audio_sources[int(selected_mic)],
                           selected_context=selected_context)

def background_recognition():
    """
    Run speech recognition in a background thread and emit results to the client in real-time.
    """
    global lumino_instance
    try:
        if lumino_instance is None:
            lumino_instance = Lumino()

        last_speech_text_length = len(lumino_instance.speech_text)
        # Continuously get recognition results from the speech_recognition generator
        for text, translation, context in lumino_instance.speech_recognition():
            # Check if the thread should stop
            if lumino_instance.stop_event.is_set():
                break

            current_speech_text_length = len(lumino_instance.speech_text)
            if current_speech_text_length > last_speech_text_length:
                is_new_line = True
            else:
                is_new_line = False
            last_speech_text_length = current_speech_text_length

            # Emit the recognized text and translation to the client via WebSocket
            socketio.emit('recognition_result', {
                'recognized_text': text,
                'translated_text': translation,
                'generated_context': context,
                'language': lumino_instance.spoken_language,
                'is_new_line': is_new_line
            })

    except Exception as e:
        # If an error occurs, emit the error message to the client
        socketio.emit('error', {'error': str(e)})

@socketio.on('start_recognition')
def handle_start_recognition():
    """
    Handle the 'start_recognition' event from the client to start the speech recognition thread.
    """
    global recognition_thread, thread_stop_event, lumino_instance
    if recognition_thread is None or not recognition_thread.is_alive():
        # Reset stop event
        lumino_instance.reset_stop_event()
        # If no thread is running, create a new one along with a stop event
        recognition_thread = Thread(target=background_recognition)  # Create the background thread
        recognition_thread.start()  # Start the thread
        # Send a status message to the client
        emit('status', {'status': 'Recognition started'})
    else:
        # If the thread is already running, notify the client
        emit('status', {'status': 'Recognition already running'})

@socketio.on('stop_recognition')
def handle_stop_recognition():
    """
    Handle the 'stop_recognition' event from the client to stop the speech recognition thread.
    """
    global recognition_thread, lumino_instance
    if recognition_thread and recognition_thread.is_alive():
        # If the thread is running, stop it
        lumino_instance.stop_recognition()
        recognition_thread.join()
        recognition_thread = None
        # Send a status message to the client
        emit('status', {'status': 'Recognition stopped'})
    else:
        emit('status', {'status': 'No recognition to stop'})

@socketio.on('switch_language')
def handle_switch_language():
    """
    Handle the 'switch_language' event from the client to switch the speaking language.
    """
    global recognition_thread
    can_switch = not (recognition_thread and recognition_thread.is_alive())
    emit('can_switch_language', {'can_switch': can_switch})

@socketio.on('confirm_switch_language')
def handle_confirm_switch_language():
    """
    Confirm language switch after user accepts the prompt.
    """
    global lumino_instance
    if lumino_instance.spoken_language == 'EN':
        new_language = 'ZH'
    else:
        new_language = 'EN'
    # Switch the language and emit the new language to the client
    lumino_instance = Lumino()
    lumino_instance.set_language(new_language)
    emit('language_switched', {'new_language': new_language})

@socketio.on('disconnect')
def handle_disconnect():
    """
    Handle the client's disconnection event to ensure the speech recognition thread is stopped.
    """
    handle_stop_recognition()  # Call the function to stop recognition
    print('Client disconnected')  # Log the disconnection on the server side

if __name__ == '__main__':
    # Run the Flask application with SocketIO support, enabling debug mode
    socketio.run(app, debug=True)

