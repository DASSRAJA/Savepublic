import sqlite3

DATABASE = 'ebooks.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ebooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        language TEXT NOT NULL,
        description TEXT NOT NULL,
        creator TEXT NOT NULL,
        filepath TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

def insert_ebook(title, author, language, description, creator, filepath):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO ebooks (title, author, language, description, creator, filepath)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (title, author, language, description, creator, filepath))
    conn.commit()
    conn.close()

def get_all_ebooks():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ebooks')
    ebooks = cursor.fetchall()
    conn.close()
    return ebooks

create_tables()
