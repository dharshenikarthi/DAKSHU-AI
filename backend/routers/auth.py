from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, UserPreference
from backend.schemas import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
from backend.auth import verify_password, get_password_hash, create_access_token
from backend.config import settings

router = APIRouter(prefix=f"{settings.API_PREFIX}/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(req: UserRegisterRequest, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # Create new user
    new_user = User(
        full_name=req.full_name.strip(),
        email=req.email.lower().strip(),
        password_hash=get_password_hash(req.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Initialize default user preferences
    prefs = UserPreference(
        user_id=new_user.id,
        preferred_language="tanglish",
        response_style="friendly",
        voice_enabled=True
    )
    db.add(prefs)
    db.commit()

    token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email})

    # Set secure cookie
    response.set_cookie(
        key="dakshu_access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )

@router.post("/login", response_model=TokenResponse)
def login(req: UserLoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token(data={"sub": str(user.id), "email": user.email})

    # Set secure cookie
    response.set_cookie(
        key="dakshu_access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="dakshu_access_token")
    return {"message": "Logged out successfully"}

