from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- Auth Schemas ---
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    idToken: Optional[str] = None
    refreshToken: Optional[str] = None
    email: Optional[str] = None
    localId: Optional[str] = None
    message: Optional[str] = None

class TokenRequest(BaseModel):
    token: str

class UserResponse(BaseModel):
    uid: str
    email: Optional[str] = None
    email_verified: bool = False

# --- Conversation Schemas ---
class CreateConversationResponse(BaseModel):
    id: str
    title: str

class ConversationItem(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

class ConversationListResponse(BaseModel):
    total: int
    conversations: List[ConversationItem]

class MessageItem(BaseModel):
    id: str
    role: str
    content_type: str
    content: str
    timestamp: datetime

class ConversationDetailResponse(BaseModel):
    id: str
    title: str
    messages: List[MessageItem]

# --- Predict Schemas ---
class PredictResponse(BaseModel):
    success: bool
    label: Optional[str] = None
    location_name: Optional[str] = None
    inliers: int
    processing_time: float

class HealthResponse(BaseModel):
    status: str
    device: str
    faiss_ready: bool
    total_vectors: int
    total_labels: int
