from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Memory
from backend.schemas import MemoryCreate, MemoryResponse, UserPreferenceResponse, UserPreferenceUpdate
from backend.auth import get_current_user
from backend.memory_service import memory_service
from backend.config import settings

router = APIRouter(prefix=f"{settings.API_PREFIX}/memories", tags=["Personal Memory"])

@router.get("", response_model=List[MemoryResponse])
def get_user_memories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all explicit personal memories saved for the user."""
    return memory_service.get_memories(db, current_user.id)

@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
def create_memory(
    req: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Explicitly save a memory fact for Dakshu to remember."""
    if not req.memory_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Memory text cannot be empty."
        )
    return memory_service.add_memory(db, current_user.id, req.memory_text)

@router.delete("/{memory_id}", status_code=status.HTTP_200_OK)
def delete_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an individual user memory."""
    success = memory_service.delete_memory(db, current_user.id, memory_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found or not owned by user."
        )
    return {"message": "Memory deleted successfully", "id": memory_id}

@router.get("/preferences", response_model=UserPreferenceResponse)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user preferences (preferred language, style, voice)."""
    return memory_service.get_user_preferences(db, current_user.id)

@router.put("/preferences", response_model=UserPreferenceResponse)
def update_preferences(
    updates: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user preferences (language, style, voice toggle)."""
    return memory_service.update_user_preferences(db, current_user.id, updates)

