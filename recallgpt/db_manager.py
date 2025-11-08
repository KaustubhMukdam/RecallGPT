import sqlite3
import datetime
import threading

class DBManager:
    def __init__(self, db_file='recallgpt.db'):
        self.db_file = db_file  # Store filename, NOT connection
        self.local = threading.local()
        self.setup_db()
    
    @property
    def conn(self):
        """Get thread-local database connection"""
        if not hasattr(self.local, 'connection') or self.local.connection is None:
            self.local.connection = sqlite3.connect(
                self.db_file,
                check_same_thread=False  # Allow cross-thread access
            )
        return self.local.connection
    
    def setup_db(self):
        """Initialize database schema"""
        cur = self.conn.cursor()
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS threads (
                thread_id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_name TEXT,
                created_at TEXT
            )
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                msg_id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id INTEGER,
                role TEXT,
                content TEXT,
                embedding BLOB,
                user_id TEXT,
                timestamp TEXT,
                FOREIGN KEY(thread_id) REFERENCES threads(thread_id)
            )
        ''')
        
        self.conn.commit()
    
    def create_thread(self, thread_name):
        """Create a new thread"""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO threads (thread_name, created_at) VALUES (?, ?)",
            (thread_name, datetime.datetime.now().isoformat())
        )
        self.conn.commit()
        return cur.lastrowid
    
    def add_message(self, thread_id, role, content, embedding=None, user_id=None, timestamp=None):
        """Add a message to a thread"""
        if timestamp is None:
            timestamp = datetime.datetime.now().isoformat()
        
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO messages (thread_id, role, content, embedding, user_id, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (thread_id, role, content, embedding, user_id, timestamp)
        )
        self.conn.commit()
    
    def get_thread_history(self, thread_id, n=10):
        """Get conversation history for a thread"""
        cur = self.conn.cursor()
        cur.execute(
            '''SELECT role, content FROM messages
               WHERE thread_id=? ORDER BY msg_id DESC LIMIT ?''',
            (thread_id, n)
        )
        res = cur.fetchall()
        return res[::-1]  # Return oldest first
    
    def list_threads(self):
        """List all threads"""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT thread_id, thread_name, created_at FROM threads ORDER BY thread_id DESC"
        )
        return cur.fetchall()
