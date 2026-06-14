from fastapi import APIRouter

from app.schemas.auth import LoginRequest, LoginResponse, UserProfile


router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    user = UserProfile(
        id="user-finops-admin",
        email=payload.email,
        full_name="FinOps Operator",
        role="admin",
    )
    return LoginResponse(
        access_token="dev-token-finops-admin",
        token_type="bearer",
        user=user,
    )


@router.get("/me", response_model=LoginResponse)
def get_me() -> LoginResponse:
    user = UserProfile(
        id="user-finops-admin",
        email="operator@finops.local",
        full_name="FinOps Operator",
        role="admin",
    )
    return LoginResponse(
        access_token="dev-token-finops-admin",
        token_type="bearer",
        user=user,
    )

