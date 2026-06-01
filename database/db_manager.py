import sqlite3
from datetime import datetime
from config import DB_PATH


def connect_db():
    return sqlite3.connect(DB_PATH)


def create_table():

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS behavior_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        behavior TEXT,
        confidence REAL
    )
    """)

    conn.commit()
    conn.close()


def save_behavior(behavior, confidence):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO behavior_log
    (timestamp, behavior, confidence)
    VALUES (?, ?, ?)
    """,
    (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        behavior,
        confidence
    ))

    conn.commit()
    conn.close()
