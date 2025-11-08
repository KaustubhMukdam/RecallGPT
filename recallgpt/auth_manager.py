import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import json

# Load from .env
API_KEY_ENABLED = os.getenv("API_KEY_ENABLED", "True").lower() == "true"
API_KEYS_FILE = "api_keys.json"

class APIKeyData(BaseModel):
    """API Key model"""
    key: str
    name: str
    user_id: str
    created_at: str
    last_used: Optional[str] = None
    is_active: bool = True
    rate_limit: int = 100  # requests per hour

class KeyManager:
    """Manage API keys"""
    
    def __init__(self):
        self.keys_file = API_KEYS_FILE
        self.load_keys()
    
    def load_keys(self):
        """Load API keys from file"""
        if os.path.exists(self.keys_file):
            try:
                with open(self.keys_file, 'r') as f:
                    self.api_keys = json.load(f)
            except:
                self.api_keys = {}
        else:
            self.api_keys = {}
    
    def save_keys(self):
        """Save API keys to file"""
        with open(self.keys_file, 'w') as f:
            json.dump(self.api_keys, f, indent=2)
    
    def generate_key(self, user_id: str, name: str, rate_limit: int = 100) -> str:
        """Generate new API key"""
        api_key = f"recallgpt_{secrets.token_urlsafe(32)}"
        
        self.api_keys[api_key] = {
            "name": name,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "is_active": True,
            "rate_limit": rate_limit
        }
        
        self.save_keys()
        return api_key
    
    def validate_key(self, api_key: str) -> dict:
        """Validate API key"""
        if api_key not in self.api_keys:
            return None
        
        key_data = self.api_keys[api_key]
        
        if not key_data.get("is_active", False):
            return None
        
        # Update last_used
        self.api_keys[api_key]["last_used"] = datetime.now().isoformat()
        self.save_keys()
        
        return key_data
    
    def revoke_key(self, api_key: str) -> bool:
        """Revoke API key"""
        if api_key in self.api_keys:
            self.api_keys[api_key]["is_active"] = False
            self.save_keys()
            return True
        return False
    
    def list_keys(self, user_id: str) -> list:
        """List all keys for a user"""
        return [
            {
                "key": key.replace(key[10:-5], "*" * (len(key) - 15)),  # Mask middle
                "name": data["name"],
                "created_at": data["created_at"],
                "is_active": data["is_active"]
            }
            for key, data in self.api_keys.items()
            if data["user_id"] == user_id
        ]
    
    def delete_key(self, api_key: str, user_id: str) -> bool:
        """Delete API key (only owner can delete)"""
        if api_key in self.api_keys:
            if self.api_keys[api_key]["user_id"] == user_id:
                del self.api_keys[api_key]
                self.save_keys()
                return True
        return False

# Global key manager
key_manager = KeyManager()

# FastAPI security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)) -> dict:
    """Verify API key from header"""
    if not API_KEY_ENABLED:
        return {"user_id": "public", "name": "public"}
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key required. Use header: X-API-Key"
        )
    
    key_data = key_manager.validate_key(api_key)
    
    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )
    
    return key_data
