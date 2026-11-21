from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


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


class PasswordResetToken(SQLModel, table=True):
    __tablename__: str = "password_reset_token"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token: str = Field(unique=True, index=True)
    expires_at: datetime
    used: bool = Field(default=False)
