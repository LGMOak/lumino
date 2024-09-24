from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from lumino import Lumino
from threading import Thread, Event

# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'  # Set the secret key for session management
socketio = SocketIO(app)  # Wrap the app with SocketIO to enable WebSocket support

# Global variables to manage the Lumino instance and threading
lumino_instance = None        # Holds the instance of the Lumino class
recognition_thread = None     # The background thread that runs speech recognition
thread_stop_event = None      # Event to signal the thread to stop

@app.route('/')
def index():
    """
    Handle the root URL and render the main page.
    """
    return render_template('index.html')

def background_recognition():
    """
    Run speech recognition in a background thread and emit results to the client in real-time.
    """
    global lumino_instance
    try:
        # Check if a Lumino instance already exists; if not, create one
        if lumino_instance is None:
            lumino_instance = Lumino()

        # Continuously get recognition results from the speech_recognition generator
        for text, translation, context in lumino_instance.speech_recognition():
            # Check if the thread should stop
            if thread_stop_event.is_set():
                break

            # Emit the recognized text and translation to the client via WebSocket
            socketio.emit('recognition_result', {
                'recognized_text': text,
                'translated_text': translation,
                'generated_context': context
            })
    except Exception as e:
        # If an error occurs, emit the error message to the client
        socketio.emit('error', {'error': str(e)})

@socketio.on('start_recognition')
def handle_start_recognition():
    """
    Handle the 'start_recognition' event from the client to start the speech recognition thread.
    """
    global recognition_thread, thread_stop_event
    if recognition_thread is None or not recognition_thread.is_alive():
        # If no thread is running, create a new one along with a stop event
        thread_stop_event = Event()  # Initialize the stop event
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
    global thread_stop_event
    if thread_stop_event:
        # Set the stop event to signal the thread to exit
        thread_stop_event.set()
        # Send a status message to the client
        emit('status', {'status': 'Recognition stopped'})
    else:
        # If no thread is running, notify the client
        emit('status', {'status': 'No recognition to stop'})

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

