import sqlite3
import os
from datetime import datetime

DB_NAME = os.path.join(os.path.dirname(__file__), "drivhus.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT,
        soil_moisture INTEGER,
        temperature INTEGER,
        humidity INTEGER,
        nitrogen INTEGER,
        phosphorus INTEGER,
        potassium INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT,
        description TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_measurement(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO measurements 
    (time, soil_moisture, temperature, humidity, nitrogen, phosphorus, potassium)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%H:%M"),
        data["soil_moisture"],
        data["temperature"],
        data["humidity"],
        data["nitrogen"],
        data["phosphorus"],
        data["potassium"]
    ))

    conn.commit()
    conn.close()


def get_history(limit=10):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT time, soil_moisture, temperature, humidity 
    FROM measurements 
    ORDER BY id DESC 
    LIMIT ?
    """, (limit,))

    rows = c.fetchall()
    conn.close()

    return [
        {
            "time": r[0],
            "soil_moisture": r[1],
            "temperature": r[2],
            "humidity": r[3],
        }
        for r in rows
    ]


def save_event(description):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO events (time, description)
    VALUES (?, ?)
    """, (datetime.now().strftime("%H:%M"), description))

    conn.commit()
    conn.close()


def get_events(limit=10):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT time, description 
    FROM events 
    ORDER BY id DESC 
    LIMIT ?
    """, (limit,))

    rows = c.fetchall()
    conn.close()

    return [
        {"time": r[0], "description": r[1]}
        for r in rows
    ]