from fastapi import Depends, Header, HTTPException, Request, status

from app.core.config import get_settings
from app.core.security import decode_access_token


def get_database(request: Request):
    return request.app.state.database


def get_queue(request: Request):
    return request.app.state.queue


def get_vector_store(request: Request):
    return request.app.state.vector_store


def get_assistant_service(request: Request):
    return request.app.state.assistant_service


def get_embedding_provider(request: Request):
    return request.app.state.embedding_provider


def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid bearer token.",
        )

    token = authorization.split(" ", maxsplit=1)[1]
    settings = get_settings()
    try:
        payload = decode_access_token(token, settings.auth_secret_key)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        ) from exc

    user = request.app.state.database.fetch_user_by_id(payload["sub"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for access token.",
        )
    return user


def get_active_tenant(
    request: Request,
    current_user: dict = Depends(get_current_user),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
):
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-Id header is required.",
        )

    if not request.app.state.database.user_has_tenant(current_user["id"], x_tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The current user cannot access the requested tenant.",
        )
    return x_tenant_id
