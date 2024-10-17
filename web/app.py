from flask import Flask, render_template, request, session, send_file
from flask_socketio import SocketIO, emit
from lumino import Lumino
from threading import Thread
from speech_recognition import Microphone
import time
import json

# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'  # Set the secret key for session management
socketio = SocketIO(app)  # Wrap the app with SocketIO to enable WebSocket support

# Global variables to manage the Lumino instance and threading
lumino_instance = Lumino()        # Holds the instance of the Lumino class
recognition_thread = None         # The background thread that runs speech recognition
audio_sources = Microphone.list_microphone_names()  # List of available microphones

@app.route("/manifest.json")
def serve_manifest():
    """
    Serve the manifest.json file to support Progressive Web App (PWA) features.
    
    Returns:
        The manifest.json file.
    """
    return send_file('manifest.json', mimetype='application/manifest+json')

@app.route('/sw.js')
def serve_sw():
    """
    Serve the service worker JavaScript file.
    
    Returns:
        The service worker JavaScript file.
    """
    return send_file('static/sw.js', mimetype='application/javascript')

@app.route('/')
def index():
    """
    Handle the root URL and render the main page.
    
    The main page allows users to select a microphone, set a context, and select the language.
    These selections are saved in the session for subsequent requests.
    
    Returns:
        Rendered HTML template for the index page.
    """
    selected_microphone = session.get('microphone', 0)  # Get the selected microphone from the session
    selected_context = session.get('context', 'General')  # Get the selected context from the session
    selected_language = session.get('lang', 'EN')  # Get the selected language from the session

    scenarios = lumino_instance.get_scenarios()  # Get available scenarios for translation

    # Update session with selected microphone, context, and language if they exist in request arguments
    if 'microphone' in request.args:
        selected_microphone = request.args.get('microphone')
        session['microphone'] = selected_microphone
        lumino_instance.set_input_source(int(selected_microphone))

    if 'context' in request.args:
        selected_context = request.args.get('context')
        session['context'] = selected_context
        lumino_instance.set_context(selected_context)

    if 'lang' in request.args:
        selected_language = request.args.get('lang')
        session['lang'] = selected_language
        lumino_instance.set_language(selected_language)

    # Render the index.html template with the selected values and options
    return render_template('index.html', language=lumino_instance.spoken_language, mics=audio_sources,
                           selected_mic=selected_microphone, mic_name=audio_sources[int(selected_microphone)],
                           selected_context=selected_context, contexts=scenarios)

def background_recognition():
    """
    Run speech recognition in a background thread and emit results to the client in real-time.
    
    Continuously listen for speech, process it, and send recognized text, translated text, and generated context
    to the client using WebSocket events.
    """
    global lumino_instance
    try:
        if lumino_instance is None:
            lumino_instance = Lumino()

        # Continuously get recognition results from the speech_recognition generator
        for text, translation, context in lumino_instance.speech_recognition():
            # Check if the thread should stop
            if lumino_instance.stop_event.is_set():
                break

            # Print recognized text and translation to the console
            print(f"Recognized Text: {text}")
            print(f"Translated Text: {translation}")

            # Emit the recognized text and translation to the client via WebSocket
            socketio.emit('recognition_result', {
                'recognized_text': text,
                'translated_text': translation,
                'generated_context': context,
                'language': lumino_instance.spoken_language,
                'is_new_line': False  # Set to False to indicate that it's part of the ongoing conversation
            })

    except Exception as e:
        # If an error occurs, emit the error message to the client
        socketio.emit('error', {'error': str(e)})

@socketio.on('start_recognition')
def handle_start_recognition():
    """
    Handle the 'start_recognition' event from the client to start the speech recognition thread.
    
    Starts a new background thread for speech recognition if no thread is currently running.
    """
    global recognition_thread, lumino_instance
    if recognition_thread is None or not recognition_thread.is_alive():
        # Reset stop event to clear any previous stop signals
        lumino_instance.reset_stop_event()
        # Set the input source to the selected microphone from the session
        selected_microphone = session.get('microphone', 0)
        lumino_instance.set_input_source(int(selected_microphone))
        # Create and start a new thread for speech recognition
        recognition_thread = Thread(target=background_recognition)
        recognition_thread.start()
        emit('status', {'status': 'Recognition started'})  # Notify the client that recognition has started
        time.sleep(1)  # Allow time for microphone setup to complete
    else:
        emit('status', {'status': 'Recognition already running'})  # Notify if recognition is already running

@socketio.on('stop_recognition')
def handle_stop_recognition():
    """
    Handle the 'stop_recognition' event from the client to stop the speech recognition thread.
    
    Stops the speech recognition thread and clears the conversation content for a new session.
    """
    global recognition_thread, lumino_instance
    if recognition_thread and recognition_thread.is_alive():
        # Stop the recognition process
        lumino_instance.stop_recognition()
        recognition_thread.join()  # Wait for the recognition thread to finish
        recognition_thread = None  # Reset the recognition thread variable
        emit('status', {'status': 'Recognition stopped'})  # Notify the client that recognition has stopped
        # Clear the conversation content for the new session
        lumino_instance.clear_conversation()
    else:
        emit('status', {'status': 'No recognition to stop'})  # Notify if there's no recognition running

@socketio.on('switch_language')
def handle_switch_language():
    """
    Handle the 'switch_language' event from the client to switch the speaking language.
    
    Switches between English and Chinese and emits the new language status to the client.
    """
    global recognition_thread
    can_switch = not (recognition_thread and recognition_thread.is_alive())  # Allow language switch only if no recognition is running
    emit('can_switch_language', {'can_switch': can_switch})

@socketio.on('confirm_switch_language')
def handle_confirm_switch_language():
    """
    Confirm language switch after user accepts the prompt.
    
    Sets the new language and emits the confirmation to the client.
    """
    global lumino_instance
    new_language = 'ZH' if lumino_instance.spoken_language == 'EN' else 'EN'  # Toggle between English and Chinese
    lumino_instance.set_language(new_language)
    emit('language_switched', {'new_language': new_language})  # Notify the client of the new language
    emit('status', {'status': f'Language switched to {new_language}'})  # Emit status to indicate language switch

@socketio.on('disconnect')
def handle_disconnect():
    """
    Handle the client's disconnection event to ensure the speech recognition thread is stopped.
    
    Stops any ongoing recognition when the client disconnects to free up resources.
    """
    handle_stop_recognition()  # Call the function to stop recognition
    print('Client disconnected')  # Log the disconnection on the server side

if __name__ == '__main__':
    # Run the Flask application with SocketIO support, enabling debug mode for development
    socketio.run(app, debug=True)


