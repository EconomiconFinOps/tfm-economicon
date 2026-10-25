from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserProfile
