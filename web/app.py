from flask import Flask, render_template, request, jsonify
import sqlite3
import lumino
import sys

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    conn = get_db_connection()
    info = conn.execute('SELECT * FROM info').fetchall()
    conn.close()
    speech_txt = lumino.Lumino()
    return render_template('index.html', info=info)


@app.route('/about')
def about():
    return render_template('second.html')


@app.route('/hello', methods=['POST'])
def hello():
    name = request.form['name']
    return render_template('hello.html', name=name)

# API endpoint to return translated  text
@app.route('/translate', methods=['POST'])
def translate():
    lumino = Lumino()
    recognized_text = lumino.speech_recog()

    if recognized_text and recognized_text.strip():
        translated_text = lumino.translate(text=recognized_text)
        # Return a JSON response 
        return jsonify(success=True, translation=translated_text)
    else:
        return jsonify(success=False, error="Speech recognition failed")


if __name__ == '__main__':
    app.run()
