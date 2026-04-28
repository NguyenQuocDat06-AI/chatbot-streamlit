from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Auth Schemas ---
class TokenRequest(BaseModel):
    token: str

class UserResponse(BaseModel):
    uid: str
    email: Optional[str] = None
    email_verified: bool = False

# --- Predict/Chat Schemas ---
class PredictResponse(BaseModel):
    success: bool
    label: Optional[str] = None
    location_name: Optional[str] = None
    inliers: int
    processing_time: float

class ChatHistoryItem(BaseModel):
    id: str
    user_id: str
    image_url: Optional[str] = None 
    file_name: Optional[str] = None
    location_name: Optional[str] = None
    inliers: Optional[int] = 0
    processing_time: Optional[float] = 0.0
    timestamp: datetime

class ChatHistoryResponse(BaseModel):
    total: int
    history: List[ChatHistoryItem]

class HealthResponse(BaseModel):
    status: str
    device: str
    faiss_ready: bool
    total_vectors: int
    total_labels: int
