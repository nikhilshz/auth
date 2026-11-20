import secrets
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import select

from database import SessionDep, create_db_and_tables
from models import (
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetToken,
    RevokedSession,
    User,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from security import (
    DUMMY_HASH,
    REFRESH_TOKEN_EXPIRATION_TIME_IN_DAYS,
    create_access_token,
    create_refresh_token,
    decode_token,
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

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise invalid_token_exception

    session_id = payload.get("sid")
    if not session_id or session.get(RevokedSession, session_id):
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

    data = {"sub": existing_user.email, "sid": str(uuid4())}
    access_token = create_access_token(data=data)
    refresh_token = create_refresh_token(data=data)

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer",
    }


# @app.get("/test-token")
# def test_token(token: Annotated[str, Depends(oauth2_scheme)]):
#     return {"token": token}

@app.post("/token/refresh")
def refresh_token(session: SessionDep, refresh_token: Annotated[str, Body(embed=True)]):
    invalid_exception_token = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
    )

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise invalid_exception_token

    session_id = payload.get("sid")
    if not session_id or session.get(RevokedSession, session_id):
        raise invalid_exception_token

    email = payload.get("sub")
    if not email:
        raise invalid_exception_token

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise invalid_exception_token

    new_access_token = create_access_token(
        data={"sub": user.email, "sid": session_id}
    )
    return {"access_token": new_access_token, "token_type": "bearer"}


@app.post("/logout")
def logout(
    session: SessionDep,
    current_user: CurrentUser,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session_id = payload.get("sid")
    if (
        not session_id
        or payload.get("sub") != current_user.email
        or session.get(RevokedSession, session_id)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = datetime.now(UTC)
    expired_sessions = session.exec(
        select(RevokedSession).where(RevokedSession.expires_at <= now)
    ).all()
    for expired_session in expired_sessions:
        session.delete(expired_session)

    session.add(
        RevokedSession(
            session_id=session_id,
            expires_at=now + timedelta(days=REFRESH_TOKEN_EXPIRATION_TIME_IN_DAYS),
        )
    )
    session.commit()
    return {"detail": "Logged out"}


user_router = APIRouter(dependencies= [Depends(get_current_user)], tags=["users"])

@user_router.get("/me", status_code=status.HTTP_200_OK, response_model=UserResponse)
def get_me(current_user: CurrentUser):
    return current_user

@user_router.patch("/me", status_code=status.HTTP_200_OK, response_model=UserResponse)
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


@user_router.get("/dashboard")
def dashboard():
    return {"Profit": 1_00_000}

app.include_router(user_router)

@app.post("/password-reset/request")
def request_password_reset(session: SessionDep, payload: PasswordResetRequest):
    message = {
        "message": "If an account exists with this email, a reset link has been sent"
    }

    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not user.id:
        return message

    token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(token=token, user_id=user.id, expires_at=datetime.now(UTC) + timedelta(minutes=10), used=False)

    session.add(reset_token)
    session.commit()
    # Send an email, her's your link:
    # /my_reset/?token=nfelbnlgbn...

    return message

@app.post("/password-reset/confirm")
def confirm_password_reset(session: SessionDep, payload: PasswordResetConfirm):
    invalid_token_error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token"
    )
    reset_token = session.exec(select(PasswordResetToken).where(PasswordResetToken.token == payload.token)).first()

    if not reset_token:
        raise invalid_token_error

    if reset_token.used:
        raise invalid_token_error

    token_expired = reset_token.expires_at < datetime.now(UTC).replace(tzinfo=None)
    if token_expired:
        raise invalid_token_error

    user = session.get(User, reset_token.user_id)
    if not user:
        raise invalid_token_error

    user.hashed_password = hash_password(payload.new_password)
    session.add(user)

    reset_token.used = True
    session.add(reset_token)

    session.commit()

    return {"message": "Password reset successfully"}