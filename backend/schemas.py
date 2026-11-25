from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# --- Auth Schemas ---
class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120, description="User's full name")
    email: EmailStr = Field(..., description="Valid unique email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (at least 6 characters)")

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Preferences & Profile Schemas ---
class UserPreferenceUpdate(BaseModel):
    preferred_language: Optional[str] = Field(None, description="tanglish, tamil, or english")
    response_style: Optional[str] = Field(None, description="friendly, concise, detailed, motivational")
    voice_enabled: Optional[bool] = None

class UserPreferenceResponse(BaseModel):
    id: int
    user_id: int
    preferred_language: str
    response_style: str
    voice_enabled: bool

    model_config = ConfigDict(from_attributes=True)

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=6, max_length=128)

class UserProfileResponse(BaseModel):
    id: int
    full_name: str
    email: str
    created_at: datetime
    preferences: Optional[UserPreferenceResponse] = None

    model_config = ConfigDict(from_attributes=True)

# --- Memory Schemas ---
class MemoryCreate(BaseModel):
    memory_text: str = Field(..., min_length=1, max_length=1000, description="Explicit personal fact or preference")

class MemoryResponse(BaseModel):
    id: int
    user_id: int
    memory_text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Conversation & Message Schemas ---
class ConversationCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []

# --- Chat Request & Response Schemas ---
class ChatRequest(BaseModel):
    conversation_id: Optional[int] = Field(None, description="Optional conversation ID; creates one if omitted")
    message: str = Field(..., min_length=1, max_length=10000, description="User prompt")
    module: Optional[str] = Field("companion", description="companion, study, english, ideas, motivation, voice")
    preferred_language: Optional[str] = Field(None, description="tanglish, tamil, english")
    client_timezone: Optional[str] = Field(None, description="Client browser timezone, e.g. Asia/Kolkata")
    client_location: Optional[str] = Field(None, description="User city or region, e.g. Chennai, India")
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    role: str = "assistant"
    content: str
    module: str
    created_at: datetime

# --- Health Check ---
class HealthResponse(BaseModel):
    status: str
    version: str
    ai_backend: str
    ai_model: str
    database: str
    timestamp: str
