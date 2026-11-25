from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, UserPreference
from backend.schemas import UserProfileResponse, UserProfileUpdate, UserPreferenceResponse
from backend.auth import get_current_user, verify_password, get_password_hash
from backend.config import settings

router = APIRouter(prefix=f"{settings.API_PREFIX}/profile", tags=["User Profile"])

@router.get("", response_model=UserProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if not prefs:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)

    return UserProfileResponse(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        created_at=current_user.created_at,
        preferences=UserPreferenceResponse.model_validate(prefs)
    )

@router.put("", response_model=UserProfileResponse)
def update_profile(
    updates: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if updates.full_name:
        current_user.full_name = updates.full_name.strip()

    if updates.email and updates.email.lower().strip() != current_user.email:
        existing = db.query(User).filter(User.email == updates.email.lower().strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already in use by another account."
            )
        current_user.email = updates.email.lower().strip()

    if updates.new_password:
        if not updates.current_password or not verify_password(updates.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect."
            )
        current_user.password_hash = get_password_hash(updates.new_password)

    db.commit()
    db.refresh(current_user)

    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    return UserProfileResponse(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        created_at=current_user.created_at,
        preferences=UserPreferenceResponse.model_validate(prefs) if prefs else None
    )

