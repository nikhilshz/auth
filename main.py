from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import select

from database import SessionDep, create_db_and_tables
from models import User, UserCreate, UserResponse, UserUpdate
from security import (
    DUMMY_HASH,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


def get_current_user(
    session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]
):
    invalid_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if not payload:
        raise invalid_token_exception

    email = payload.get("sub")
    if not email:
        raise invalid_token_exception

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise invalid_token_exception

    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

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

    access_token = create_access_token(data={"sub": existing_user.email})

    return {"access_token": access_token, "token_type": "bearer"}


# @app.get("/test-token")
# def test_token(token: Annotated[str, Depends(oauth2_scheme)]):
#     return {"token": token}

@app.get("/me", status_code=status.HTTP_200_OK, response_model=UserResponse)
def me(current_user: CurrentUser):
    return current_user

@app.patch("/me", status_code=status.HTTP_200_OK, response_model=UserResponse)
def update_me(session: SessionDep, current_user: CurrentUser, update_payload: UserUpdate):
    if not update_payload.email:
        return current_user
    user_with_email = session.exec(select(User).where(User.email == update_payload.email)).first()

    if user_with_email and user_with_email.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already taken"
        )
    current_user.email = update_payload.email

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return current_user