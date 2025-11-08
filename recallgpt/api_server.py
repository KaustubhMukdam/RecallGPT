from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from memory_manager import MemoryManager
from llm_interface import LLMInterface
import uvicorn
import threading
from auth_manager import verify_api_key
from auth_routes import router as auth_router
import os
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Load environment variables
load_dotenv()


# Initialize app
app = FastAPI(
    title="RecallGPT API",
    description="AI chatbot with long-term memory and semantic retrieval",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add auth routes
app.include_router(auth_router)

# Thread-safe singleton pattern for memory and LLM
_memory = None
_llm = None
_lock = threading.Lock()

def get_memory():
    """Get or create memory manager (thread-safe)"""
    global _memory
    if _memory is None:
        with _lock:
            if _memory is None:
                _memory = MemoryManager("recallgpt.db")
    return _memory

def get_llm():
    """Get or create LLM interface (thread-safe)"""
    global _llm
    if _llm is None:
        with _lock:
            if _llm is None:
                _llm = LLMInterface(model_name="qwen2.5-coder:1.5b")
    return _llm

# Request/Response Models
class ThreadCreateRequest(BaseModel):
    thread_name: str
    user_id: Optional[str] = None

class ThreadCreateResponse(BaseModel):
    thread_id: int
    thread_name: str
    message: str

class ChatRequest(BaseModel):
    thread_id: int
    message: str
    max_tokens: Optional[int] = 2000
    top_k: Optional[int] = 100

class ChatResponse(BaseModel):
    thread_id: int
    user_message: str
    assistant_response: str
    retrieved_messages: int
    token_count: int

class ThreadListResponse(BaseModel):
    threads: List[dict]
    total: int

class AnalyticsResponse(BaseModel):
    total_retrievals: int
    avg_retrieved_messages: float
    avg_token_count: float
    avg_response_length: float
    total_tokens_used: int
    threads_accessed: int
    retrieval_methods: dict

# API Endpoints
# Serve static files (add this before other routes)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_ui():
    """Serve the web UI"""
    return FileResponse("static/index.html")


# @app.get("/")
# def root():
#     """Root endpoint - API status"""
#     return {
#         "message": "RecallGPT API is running",
#         "version": "1.0.0",
#         "docs": "/docs"
#     }

@app.post("/threads/create", response_model=ThreadCreateResponse)
def create_thread(request: ThreadCreateRequest, key_data: dict = Depends(verify_api_key)):
    """Create a new conversation thread"""
    try:
        memory = get_memory()
        thread_id = memory.create_thread(request.thread_name)
        return ThreadCreateResponse(
            thread_id=thread_id,
            thread_name=request.thread_name,
            message="Thread created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/threads/list", response_model=ThreadListResponse)
def list_threads(key_data: dict = Depends(verify_api_key)):
    """List all conversation threads"""
    try:
        memory = get_memory()
        threads = memory.list_threads()
        thread_list = [
            {
                "thread_id": tid,
                "thread_name": tname,
                "created_at": tcreated
            }
            for tid, tname, tcreated in threads
        ]
        return ThreadListResponse(
            threads=thread_list,
            total=len(thread_list)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, key_data: dict = Depends(verify_api_key)):
    """Send a message and get AI response with memory"""
    try:
        memory = get_memory()
        llm = get_llm()
        
        # Add user message
        memory.add_message(request.thread_id, "user", request.message)
        
        # Retrieve MORE relevant history
        relevant_history = memory.get_hybrid_matches_with_token_limit(
            request.thread_id,
            request.message,
            top_k=20,  # ✅ Retrieve up to 20 messages
            max_tokens=request.max_tokens or 3000
        )
        
        # Build better prompt with clear structure
        # Add at the start of the prompt
        prompt = """You are RecallGPT, an AI assistant with perfect memory. 

        IMPORTANT RULES:
        1. Always use conversation history to provide personalized responses
        2. Reference previous facts the user shared (name, preferences, work, etc.)
        3. Never give generic responses when you have context
        4. Be conversational and acknowledge what you know about the user

        === Conversation History ===
        """

        prompt += "\n\nWhen answering, EXPLICITLY reference relevant context from conversation history."
        
        if relevant_history:
            prompt += "=== Conversation History ===\n"
            for role, content in relevant_history:
                prompt += f"{role.capitalize()}: {content}\n\n"
        
        prompt += "=== Current Question ===\n"
        prompt += f"User: {request.message}\n\n"
        prompt += "Assistant:"
        
        # Generate response
        response = llm.generate(prompt)
        memory.add_message(request.thread_id, "assistant", response)
        
        # Log retrieval
        token_count = memory.count_tokens(prompt)
        memory.logger.log_retrieval(
            thread_id=request.thread_id,
            query=request.message,
            retrieved_count=len(relevant_history),
            token_count=token_count,
            response_length=len(response),
            retrieval_method="hybrid_token_limited",
            context_msgs=relevant_history
        )
        
        return ChatResponse(
            thread_id=request.thread_id,
            user_message=request.message,
            assistant_response=response,
            retrieved_messages=len(relevant_history),
            token_count=token_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/threads/{thread_id}/history")
def get_thread_history(thread_id: int, limit: int = 10, key_data: dict = Depends(verify_api_key)):
    """Get conversation history for a thread"""
    try:
        memory = get_memory()
        history = memory.get_recent_history(thread_id, n=limit)
        return {
            "thread_id": thread_id,
            "messages": [
                {"role": role, "content": content}
                for role, content in history
            ],
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(key_data: dict = Depends(verify_api_key)):
    """Get system analytics and usage statistics"""
    try:
        memory = get_memory()
        stats, logs = memory.logger.get_stats()
        
        if not stats:
            return AnalyticsResponse(
                total_retrievals=0,
                avg_retrieved_messages=0.0,
                avg_token_count=0.0,
                avg_response_length=0.0,
                total_tokens_used=0,
                threads_accessed=0,
                retrieval_methods={}
            )
        return AnalyticsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "model": "loaded"
    }

# Run server
if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
