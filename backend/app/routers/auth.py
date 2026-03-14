from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User, UserRole, UserSession
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserProfile
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/seed-admin", response_model=MessageResponse)
def seed_admin(db: Session = Depends(get_db)) -> MessageResponse:
    existing = db.scalar(select(User).where(User.email == "admin@example.com"))
    if existing:
        existing.password_hash = get_password_hash("Admin@123")
        existing.role = UserRole.admin
        existing.department = existing.department or "Legal"
        existing.gcc_location = existing.gcc_location or "HQ"
        existing.is_active = True
        db.commit()
        return MessageResponse(message="Seed admin reset: admin@example.com / Admin@123")

    user = User(
        email="admin@example.com",
        password_hash=get_password_hash("Admin@123"),
        role=UserRole.admin,
        department="Legal",
        gcc_location="HQ",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return MessageResponse(message="Seed admin created: admin@example.com / Admin@123")


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email, User.is_active.is_(True)))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    expires_at = datetime.now(UTC) + timedelta(minutes=settings.refresh_token_expire_minutes)
    session = UserSession(user_id=user.id, jwt_token=refresh_token, expires_at=expires_at)
    db.add(session)
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        token_data = decode_token(payload.refresh_token)
        if token_data.get("type") != "refresh":
            raise ValueError("Invalid token type")
        user_id = int(token_data["sub"])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    session = db.scalar(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.jwt_token == payload.refresh_token,
            UserSession.expires_at > datetime.now(UTC),
        )
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session not found")

    access_token = create_access_token(str(user_id))
    new_refresh_token = create_refresh_token(str(user_id))
    session.jwt_token = new_refresh_token
    session.expires_at = datetime.now(UTC) + timedelta(minutes=settings.refresh_token_expire_minutes)
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.get("/profile", response_model=UserProfile)
def profile(current_user: User = Depends(get_current_user)) -> UserProfile:
    return UserProfile.model_validate(current_user)


@router.post("/logout", response_model=MessageResponse)
def logout(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MessageResponse:
    session = db.scalar(select(UserSession).where(UserSession.jwt_token == payload.refresh_token))
    if session:
        db.delete(session)
        db.commit()
    return MessageResponse(message="Logged out")
