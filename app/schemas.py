from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class UserCreate(SQLModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=12)


class UserUpdate(SQLModel):
    email: EmailStr | None = None


class UserResponse(SQLModel):
    id: int
    email: str
    role: str


class PasswordResetRequest(SQLModel):
    email: EmailStr


class PasswordResetConfirm(SQLModel):
    token: str
    new_password: str = Field(min_length=1, max_length=12)
