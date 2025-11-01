import sqlite3
import datetime

class DBManager:
    def __init__(self, db_file='recallgpt.db'):
        self.conn = sqlite3.connect(db_file)
        self.setup_db()

    def setup_db(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS threads (
            thread_id INTEGER PRIMARY KEY, thread_name TEXT, created_at TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS messages (
            msg_id INTEGER PRIMARY KEY, thread_id INTEGER, role TEXT, content TEXT, timestamp TEXT,
            FOREIGN KEY(thread_id) REFERENCES threads(thread_id))''')
        self.conn.commit()

    def create_thread(self, thread_name):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO threads (thread_name, created_at) VALUES (?, ?)",
                    (thread_name, datetime.datetime.now().isoformat()))
        self.conn.commit()
        return cur.lastrowid

    def add_message(self, thread_id, role, content):
        cur = self.conn.cursor()
        cur.execute('''INSERT INTO messages (thread_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?)''', (thread_id, role, content, datetime.datetime.now().isoformat()))
        self.conn.commit()

    def get_thread_history(self, thread_id, n=10):
        cur = self.conn.cursor()
        cur.execute('''SELECT role, content FROM messages 
                WHERE thread_id=? ORDER BY msg_id DESC LIMIT ?''', (thread_id, n))
        res = cur.fetchall()
        return res[::-1]  # Return oldest first

    def list_threads(self):
        cur = self.conn.cursor()
        cur.execute("SELECT thread_id, thread_name, created_at FROM threads ORDER BY thread_id DESC")
        return cur.fetchall()
