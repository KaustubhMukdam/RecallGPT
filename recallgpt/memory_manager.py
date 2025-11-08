from db_manager import DBManager
from sentence_transformers import SentenceTransformer
import pickle
import numpy as np
import datetime
import json
import os
from datetime import datetime

class MemoryManager:
    def __init__(self, db_file='recallgpt.db'):
        self.db = DBManager(db_file)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.logger = RetrievalLogger()

    def create_thread(self, thread_name):
        return self.db.create_thread(thread_name)

    def add_message(self, thread_id, role, content, user_id=None):
        if role in ["user", "assistant"]:
            vector = self.model.encode(content)
            embedding_blob = pickle.dumps(vector)
        else:
            embedding_blob = None
        self.db.add_message(thread_id, role, content, embedding_blob, user_id)

    def get_recent_history(self, thread_id, n=10):
        """Get recent conversation history"""
        cur = self.db.conn.cursor()
        cur.execute(
            '''SELECT role, content FROM messages
            WHERE thread_id=? ORDER BY msg_id DESC LIMIT ?''',
            (thread_id, n)
        )
        res = cur.fetchall()
        return res[::-1]  # Return oldest first


    def list_threads(self):
        return self.db.list_threads()
    
    def get_semantic_matches(self, thread_id, query, model, top_k=5):
        # Use self.db for DB queries, just as you do everywhere else.
        cur = self.db.conn.cursor()
        cur.execute("SELECT msg_id, embedding, role, content FROM messages WHERE thread_id = ?", (thread_id,))
        records = cur.fetchall()
        
        msg_ids = []
        embeddings = []
        payloads = []
        import pickle
        for msg_id, embedding_blob, role, content in records:
            if embedding_blob:
                embedding = pickle.loads(embedding_blob)
                embeddings.append(embedding)
                msg_ids.append(msg_id)
                payloads.append((role, content))

        # Semantic similarity search
        import numpy as np
        query_emb = model.encode(query)
        scores = np.dot(embeddings, query_emb)
        top_indices = np.argsort(scores)[-top_k:][::-1]
        return [payloads[i] for i in top_indices]
    
    def get_hybrid_matches(self, thread_id, query, top_k=5, semantic_weight=0.7, recency_weight=0.3):
        """
        Hybrid retrieval: combines semantic similarity (70%) + recency (30%)
        Returns the top_k most relevant AND recent messages
        """
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT msg_id, embedding, role, content, timestamp 
            FROM messages 
            WHERE thread_id = ? 
            ORDER BY timestamp DESC
        """, (thread_id,))
        
        records = cur.fetchall()
        if not records:
            return []
        
        # Prepare data
        embeddings = []
        payloads = []
        timestamps = []
        
        for msg_id, emb_blob, role, content, ts in records:
            if emb_blob:
                try:
                    embedding = pickle.loads(emb_blob)
                    embeddings.append(embedding)
                    payloads.append((role, content))
                    timestamps.append(datetime.datetime.fromisoformat(ts))
                except Exception as e:
                    pass
        
        if not embeddings:
            return []
        
        # Convert to numpy array
        embeddings = np.array(embeddings)
        
        # Semantic similarity score (0 to 1)
        query_emb = self.model.encode(query)
        semantic_scores = np.dot(embeddings, query_emb)
        semantic_scores = (semantic_scores - np.min(semantic_scores)) / (np.max(semantic_scores) - np.min(semantic_scores) + 1e-10)
        
        # Recency score (0 to 1, newer = higher)
        now = datetime.datetime.now()
        recency_scores = np.array([
            1.0 / (1.0 + (now - ts).total_seconds() / 3600) 
            for ts in timestamps
        ])
        
        # Hybrid score = weighted combination
        hybrid_scores = (semantic_weight * semantic_scores) + (recency_weight * recency_scores)
        
        # Get top-k
        top_indices = np.argsort(hybrid_scores)[-top_k:][::-1]
        return [payloads[i] for i in top_indices]
    
    def count_tokens(self, text):
        """
        Approximate token count using a simple heuristic:
        ~4 characters = 1 token (standard OpenAI approximation)
        Adjust if using a specific tokenizer
        """
        return len(text) // 4

    def get_hybrid_matches_with_token_limit(self, thread_id, query, top_k=5, max_tokens=2000, semantic_weight=0.7, recency_weight=0.3):
        """
        Hybrid retrieval with token limit awareness.
        Returns messages that fit within max_tokens budget.
        """
        import pickle
        import numpy as np
        import datetime
        
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT msg_id, embedding, role, content, timestamp 
            FROM messages 
            WHERE thread_id = ? 
            ORDER BY timestamp ASC
        """, (thread_id,))
        
        records = cur.fetchall()
        
        if not records:
            return []
        
        # Prepare data - SKIP THE VERY LAST MESSAGE (the current query)
        embeddings = []
        payloads = []
        timestamps = []
        
        # Process all messages EXCEPT the last one (which is the current query)
        for msg_id, emb_blob, role, content, ts in records[:-1]:  # ✅ Exclude last message
            if emb_blob:
                try:
                    embedding = pickle.loads(emb_blob)
                    embeddings.append(embedding)
                    payloads.append((role, content))
                    timestamps.append(datetime.datetime.fromisoformat(ts))
                except Exception:
                    pass
        
        if not embeddings:
            return []
        
        # Convert to numpy array
        embeddings = np.array(embeddings)
        
        # Semantic similarity score
        query_emb = self.model.encode(query)
        semantic_scores = np.dot(embeddings, query_emb)
        
        # Normalize semantic scores
        if len(semantic_scores) > 1:
            semantic_scores = (semantic_scores - np.min(semantic_scores)) / (np.max(semantic_scores) - np.min(semantic_scores) + 1e-10)
        else:
            semantic_scores = np.array([1.0])
        
        # Recency score
        now = datetime.datetime.now()
        recency_scores = np.array([
            1.0 / (1.0 + (now - ts).total_seconds() / 3600) 
            for ts in timestamps
        ])
        
        # Hybrid score
        hybrid_scores = (semantic_weight * semantic_scores) + (recency_weight * recency_scores)
        
        # Sort by hybrid score (descending)
        sorted_indices = np.argsort(hybrid_scores)[::-1]
        
        # Select messages within token budget
        selected_messages = []
        token_count = self.count_tokens(query)
        
        for idx in sorted_indices:
            msg_role, msg_content = payloads[idx]
            msg_tokens = self.count_tokens(f"{msg_role}: {msg_content}\n")
            
            if token_count + msg_tokens <= max_tokens:
                selected_messages.append((msg_role, msg_content))
                token_count += msg_tokens
            else:
                break
        
        return selected_messages


def get_relevant_history(current_prompt, thread_history):
    keywords = ["stack", "queue", "tree", "graph"]  # Add more data structures as needed
    topic = None
    for word in keywords:
        if word in current_prompt.lower():
            topic = word
            break

    if topic is None:
        return thread_history[-5:]  # default to last 5, adjust as needed

    # If each history item is a tuple (role, content), filter on content
    return [msg for msg in thread_history if topic in msg[1].lower()]
    # msg[0] = role, msg[1] = content

class RetrievalLogger:
    """Logs all retrieval operations for analytics"""
    
    def __init__(self, log_file="retrieval_logs.jsonl"):
        self.log_file = log_file
        self.ensure_log_file_exists()
    
    def ensure_log_file_exists(self):
        """Create log file if it doesn't exist"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                pass
    
    def log_retrieval(self, thread_id, query, retrieved_count, token_count, 
                     response_length, retrieval_method="hybrid", context_msgs=None):
        """Log a retrieval operation"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "thread_id": thread_id,
            "query": query[:100],  # First 100 chars
            "query_length": len(query),
            "retrieved_messages": retrieved_count,
            "token_count": token_count,
            "response_length": response_length,
            "retrieval_method": retrieval_method,
            "context_preview": [msg[1][:50] for msg in context_msgs[:3]] if context_msgs else []
        }
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Error writing to log: {e}")
    
    def get_stats(self):
        """Retrieve and analyze logs"""
        if not os.path.exists(self.log_file):
            return None
        
        logs = []
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except:
                    pass
        
        if not logs:
            return None
        
        # Calculate stats
        stats = {
            "total_retrievals": len(logs),
            "avg_retrieved_messages": sum(l["retrieved_messages"] for l in logs) / len(logs),
            "avg_token_count": sum(l["token_count"] for l in logs) / len(logs),
            "avg_response_length": sum(l["response_length"] for l in logs) / len(logs),
            "total_tokens_used": sum(l["token_count"] for l in logs),
            "threads_accessed": len(set(l["thread_id"] for l in logs)),
            "retrieval_methods": {}
        }
        
        # Count retrieval methods
        for log in logs:
            method = log.get("retrieval_method", "unknown")
            stats["retrieval_methods"][method] = stats["retrieval_methods"].get(method, 0) + 1
        
        return stats, logs


