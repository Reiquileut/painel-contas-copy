from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str
    is_admin: bool = False


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    session_id: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class SessionLoginResponse(BaseModel):
    user: UserResponse
    session_expires_at: datetime


class MessageResponse(BaseModel):
    message: str
