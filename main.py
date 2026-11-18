from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from database import SessionDep, create_db_and_tables
from models import User, UserCreate, UserResponse, UserUpdate
from security import DUMMY_HASH, hash_password, verify_password


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def register(session: SessionDep, user_data: UserCreate):
    existing_user = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    new_user = User(
        email=user_data.email, hashed_password=hash_password(user_data.password)
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


@app.post("/token")
def login(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    existing_user = session.exec(
        select(User).where(User.email == form_data.username)
    ).first()

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not existing_user:
        verify_password(
            form_data.password, DUMMY_HASH
        )  # Bluff time difference between email and password
        raise credentials_exception

    if not verify_password(form_data.password, existing_user.hashed_password):
        raise credentials_exception

    return {"access_token": "jwt_placeholder", "token_type": "bearer"}
