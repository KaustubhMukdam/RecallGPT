from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from auth_manager import key_manager, verify_api_key

router = APIRouter(prefix="/auth", tags=["Authentication"])

class GenerateKeyRequest(BaseModel):
    user_id: str
    name: str
    rate_limit: int = 100

class GenerateKeyResponse(BaseModel):
    api_key: str
    message: str

@router.post("/generate-key", response_model=GenerateKeyResponse)
def generate_api_key(request: GenerateKeyRequest):
    """Generate new API key for user"""
    try:
        api_key = key_manager.generate_key(
            user_id=request.user_id,
            name=request.name,
            rate_limit=request.rate_limit
        )
        return GenerateKeyResponse(
            api_key=api_key,
            message=f"API key generated successfully. Save it securely!"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/keys")
def list_user_keys(key_data: dict = Depends(verify_api_key)):
    """List all API keys for authenticated user"""
    try:
        user_id = key_data.get("user_id")
        keys = key_manager.list_keys(user_id)
        return {
            "user_id": user_id,
            "keys": keys,
            "total": len(keys)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/revoke-key")
def revoke_api_key(api_key: str, key_data: dict = Depends(verify_api_key)):
    """Revoke an API key"""
    try:
        if key_manager.revoke_key(api_key):
            return {"message": "API key revoked successfully"}
        else:
            raise HTTPException(status_code=404, detail="API key not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-key")
def delete_api_key(api_key: str, key_data: dict = Depends(verify_api_key)):
    """Delete an API key"""
    try:
        user_id = key_data.get("user_id")
        if key_manager.delete_key(api_key, user_id):
            return {"message": "API key deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="API key not found or unauthorized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
def auth_status(key_data: dict = Depends(verify_api_key)):
    """Check API key status"""
    return {
        "authenticated": True,
        "user_id": key_data.get("user_id"),
        "name": key_data.get("name"),
        "created_at": key_data.get("created_at"),
        "last_used": key_data.get("last_used")
    }
