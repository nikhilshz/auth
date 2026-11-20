from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class UserCreate(SQLModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=12)


class User(SQLModel, table=True):
    __tablename__: str = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str
    role: str = Field(default="user")


class RevokedSession(SQLModel, table=True):
    __tablename__: str = "revoked_sessions"

    session_id: str = Field(primary_key=True)
    expires_at: datetime


class UserUpdate(SQLModel):
    email: EmailStr | None = None


class UserResponse(SQLModel):
    id: int
    email: str
    role: str
