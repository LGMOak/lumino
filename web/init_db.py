import sqlite3

connection = sqlite3.connect('database.db')


with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO info (title, content) VALUES (?, ?)",
            ('User1', 'Content for the first user')
            )

cur.execute("INSERT INTO info (title, content) VALUES (?, ?)",
            ('User2', 'Content for the second user')
            )

connection.commit()
connection.close()
