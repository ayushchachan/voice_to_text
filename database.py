import sqlite3

# Function to save transcription to the database
def save_transcription(text, start_time, stop_time):
    # Connect to the database (or create it if it doesn't exist)
    with sqlite3.connect('transcriptions.db') as conn:
        cursor = conn.cursor()
        # Create the table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT,
                stop_time TEXT,
                transcription TEXT
            )
        ''')
        # Insert the transcription record
        cursor.execute("INSERT INTO transcriptions (start_time, stop_time, transcription) VALUES (?, ?, ?)",
                       (start_time, stop_time, text))
        conn.commit()

# Function to fetch the history from the database
def fetch_history():
    with sqlite3.connect('transcriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT start_time, transcription FROM transcriptions ORDER BY start_time ASC")
        return cursor.fetchall()
