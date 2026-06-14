from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_database
from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.schemas.auth import LoginRequest, LoginResponse, UserProfile


router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, database=Depends(get_database)) -> LoginResponse:
    user = database.fetch_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    settings = get_settings()
    access_token = create_access_token(
        user_id=user["id"],
        secret_key=settings.auth_secret_key,
        expires_minutes=settings.auth_token_ttl_minutes,
    )
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserProfile(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
        ),
    )


@router.get("/me", response_model=UserProfile)
def get_me(current_user=Depends(get_current_user)) -> UserProfile:
    return UserProfile(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user["role"],
    )
