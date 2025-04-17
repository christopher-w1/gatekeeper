from pydantic import BaseModel, EmailStr
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

# Database models
class UserModel(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str
    email: str
    hashed_password: str
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_access: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Request models
class RegisterRequest(BaseModel):
    api_token: str
    username: str
    email: EmailStr
    password: str

class GetUserDataRequest(BaseModel):
    api_token: str
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    id: Optional[str] = None

class LoginRequest(BaseModel):
    api_token: str
    email: EmailStr
    password: str

class LogoutRequest(BaseModel):
    api_token: str
    session_token: str

class ModifyUserRequest(BaseModel):
    api_token: str
    session_token: str
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None