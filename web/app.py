from flask import Flask, render_template, request
import sqlite3

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
    return render_template('index.html', info=info)


@app.route('/about')
def about():
    return render_template('second.html')


@app.route('/hello', methods=['POST'])
def hello():
    name = request.form['name']
    return render_template('hello.html', name=name)


if __name__ == '__main__':
    app.run()
