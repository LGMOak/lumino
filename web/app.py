from flask import Flask, render_template, request, jsonify
import sqlite3
from lumino import Lumino

app = Flask(__name__)

lumino_instance = None

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



@app.route('/translate', methods=['POST'])
def translate():
    global lumino_instance
    try:
        # Check if an instance already exists, if not, create one
        if lumino_instance is None:
            lumino_instance = Lumino()
            

        text, translation = next(lumino_instance.speech_recognition())
        return jsonify({
            'success': True,
            'recognized_text': text,
            'translated_text': translation
        })
    except StopIteration:
        
        lumino_instance = None
        return jsonify({
            'success': False,
            'error': 'Recognition completed or needs to be restarted.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


if __name__ == '__main__':
    app.run(debug=True, threaded=True)

