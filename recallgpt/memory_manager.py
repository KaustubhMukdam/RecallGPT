from db_manager import DBManager

class MemoryManager:
    def __init__(self, db_file='recallgpt.db'):
        self.db = DBManager(db_file)

    def create_thread(self, thread_name):
        return self.db.create_thread(thread_name)

    def add_message(self, thread_id, role, content):
        self.db.add_message(thread_id, role, content)

    def get_recent_history(self, thread_id, n=10):
        return self.db.get_thread_history(thread_id, n)

    def list_threads(self):
        return self.db.list_threads()
