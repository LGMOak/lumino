from flask import Flask, render_template, request, jsonify
import sqlite3
from lumino import Lumino
import time
import sys
from threading import Thread, Event
import queue

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    #conn = get_db_connection()
    #info = conn.execute('SELECT * FROM info').fetchall()
    #conn.close()
    #speech_txt = lumino.Lumino()
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('second.html')


@app.route('/hello', methods=['POST'])
def hello():
    name = request.form['name']
    return render_template('hello.html', name=name)



def run_speech_to_text(lumino):
    lumino.speech_to_text()  

@app.route('/translate', methods=['POST'])
def translate():
    lumino = Lumino()
    # New thread to run speech_to_text
    thread = Thread(target=run_speech_to_text, args=(lumino,))
    thread.start()
    thread.join(timeout=15)  # wait for 15 seconds for the thread to finish, can be adjusted

    if lumino.speech_text:
        # If there is a recognized text
        recognized_text = ''.join(lumino.speech_text)
        translated_text = lumino.translate(text=recognized_text)
        response_data = {
            'success': True,
            'recognized_text': recognized_text,
            'translated_text': translated_text
        }
    else:
        # If no speech detected or timeout
        response_data = {
            'success': False,
            'error': 'Timeout or no speech detected'
        }

    return jsonify(response_data)


if __name__ == '__main__':
    app.run(debug=True, threaded=True)

