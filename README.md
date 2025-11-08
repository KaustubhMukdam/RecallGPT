# 🧠 Project 7/20 – RecallGPT: Enhancing Small Language Models with Persistent Long-Term Memory

*Part of my **100 Days of Code – Portfolio Project Series***

> **AI Chatbot with Long-Term Memory**  
> Intelligent conversations powered by hybrid semantic retrieval and token-aware memory management.

[![Status](https://img.shields.io/badge/Status-Active-success)](https://github.com/KaustubhMukdam/RecallGPT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

🔗 **GitHub Repo:** [RecallGPT](https://github.com/KaustubhMukdam/RecallGPT)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **Long-Term Memory** | Hybrid retrieval combining semantic similarity + recency ranking |
| 💬 **Multi-Turn Conversations** | Maintains context across 10–20+ messages seamlessly |
| 🔐 **Secure Authentication** | API key-based access for protected endpoints |
| 📊 **Analytics Dashboard** | Track usage metrics, token counts, and retrieval stats |
| 🎨 **Modern UI** | Claude/Perplexity-inspired clean chat interface |
| ⚡ **Fast & Scalable** | Token-aware context management prevents cutoffs |
| 🔄 **Thread Management** | Manage multiple conversation threads per user |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Ollama** for local LLM inference
- **4GB+ RAM** recommended

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/KaustubhMukdam/RecallGPT.git
cd RecallGPT

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: .\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Run Ollama (Required)

**1. Install Ollama**  
Download from [https://ollama.ai](https://ollama.ai)

**2. Pull the model**
```bash
ollama pull qwen2.5-coder:1.5b
```

### Start the Application

```bash
cd recallgpt
python api_server.py
```

🎉 **Open your browser at:** [http://localhost:8000](http://localhost:8000)

---

## 📂 Project Structure

```
RecallGPT/
├── recallgpt/
│   ├── api_server.py           # FastAPI REST API
│   ├── memory_manager.py       # Hybrid retrieval & memory system
│   ├── db_manager.py           # SQLite database management
│   ├── llm_interface.py        # Ollama LLM integration
│   ├── auth_manager.py         # API key authentication logic
│   ├── auth_routes.py          # Auth endpoints
│   ├── static/                 # Frontend assets
│   │   ├── index.html
│   │   ├── style.css
│   │   └── script.js
│   ├── recallgpt.db            # Auto-created SQLite DB
│   └── retrieval_logs.jsonl    # Analytics logs
├── tests/
│   ├── test_api.py
│   ├── test_token_counting.py
│   └── test_logging_analytics.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
DATABASE_URL=recallgpt.db
API_HOST=0.0.0.0
API_PORT=8000
LLM_MODEL=qwen2.5-coder:1.5b
API_KEY_ENABLED=True
SECRET_KEY=your-secret-key-here
```

---

## 📖 Usage

### Generate API Key

```bash
curl -X POST http://localhost:8000/auth/generate-key \
  -H "Content-Type: application/json" \
  -d '{"user_id": "your_id", "name": "My Key"}'
```

### Create Conversation Thread

```bash
curl -X POST http://localhost:8000/threads/create \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{"thread_name": "My Conversation"}'
```

### Send Message

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "thread_id": 1,
    "message": "Explain Python decorators",
    "max_tokens": 2000,
    "top_k": 20
  }'
```

---

## 🧠 Architecture Overview

### 🔍 Memory System

RecallGPT uses a **hybrid retrieval mechanism** combining:

1. **Semantic Search** – via Sentence Transformers (all-MiniLM-L6-v2)
2. **Recency Ranking** – prioritizes the most recent messages
3. **Hybrid Scoring** – `0.7 × semantic + 0.3 × recency`
4. **Token Window Management** – ensures context fits within model limits

### 🗄️ Database Schema

```sql
CREATE TABLE threads (
    thread_id INTEGER PRIMARY KEY,
    thread_name TEXT,
    created_at TEXT
);

CREATE TABLE messages (
    msg_id INTEGER PRIMARY KEY,
    thread_id INTEGER,
    role TEXT,
    content TEXT,
    embedding BLOB,
    user_id TEXT,
    timestamp TEXT,
    FOREIGN KEY(thread_id) REFERENCES threads(thread_id)
);
```

---

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve Web UI |
| `/health` | GET | Health check |
| `/auth/generate-key` | POST | Generate API key |
| `/threads/create` | POST | Create conversation thread |
| `/threads/list` | GET | List all threads |
| `/threads/{id}/history` | GET | Fetch conversation history |
| `/chat` | POST | Send message to chatbot |
| `/analytics` | GET | Retrieve usage analytics |

---

## 🎨 UI Features

- **🌙 Dark Mode** – Toggle theme with one click
- **📑 Thread Sidebar** – Easy navigation between conversations
- **⚡ Real-Time Chat** – Instant responses
- **📌 Context Indicator** – Shows retrieved messages count
- **🔢 Token Counter** – Track usage dynamically
- **📈 Analytics Dashboard** – Visualize performance metrics

---

## 🔒 Security

- ✅ API key authentication
- ✅ Thread-safe database connections
- ✅ Pydantic input validation
- ✅ CORS-enabled for web interface
- ✅ Secure environment-based configuration

---

## 📈 Performance

| Metric | Performance |
|--------|-------------|
| **Retrieval Speed** | <100ms for 1000+ messages |
| **Memory Usage** | ~500MB (with embeddings) |
| **Concurrent Threads** | Multiple user sessions supported |
| **Context Efficiency** | Smart token windowing prevents cutoffs |

---

## 🛠 Tech Stack

**Backend**
- FastAPI
- Python 3.11
- SQLite

**AI/ML**
- Sentence Transformers
- Ollama (Qwen, Llama)

**Frontend**
- HTML, CSS, JavaScript

**Deployment**
- Uvicorn ASGI server

---

## 📚 Learning Outcomes

Through building RecallGPT, I gained hands-on experience with:

- ✨ Building long-term memory systems for small LLMs
- 🔍 Implementing hybrid RAG pipelines with semantic + recency weighting
- ⚡ Optimizing context windows for token efficiency
- 🏗️ Creating a modular FastAPI backend with local LLM integration
- 🗄️ Designing efficient database schemas for conversational AI

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repo
2. **Create** your branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add new feature'`)
4. **Push** to your branch (`git push origin feature/AmazingFeature`)
5. **Submit** a Pull Request 🚀

---

## 📝 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Special thanks to these amazing projects:

- [Sentence Transformers](https://www.sbert.net/) – Semantic embeddings
- [Ollama](https://ollama.ai/) – Local LLM inference
- [FastAPI](https://fastapi.tiangolo.com/) – Backend framework

---

## 👨‍💻 Author

**Kaustubh Mukdam**

- GitHub: [@KaustubhMukdam](https://github.com/KaustubhMukdam)
- LinkedIn: [Kaustubh Mukdam](https://linkedin.com/in/kaustubh-mukdam)

---

<div align="center">

⭐ **If you found this project helpful, consider giving it a star!** ⭐

Made with ❤️ by Kaustubh Mukdam

</div>