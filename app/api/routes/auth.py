from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from app.api.dependencies import AccessTokenPayload, CurrentUser
from app.core.security import (
    DUMMY_HASH,
    REFRESH_TOKEN_EXPIRATION_TIME_IN_DAYS,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import SessionDep
from app.models import RevokedSession, User
from app.schemas import UserCreate, UserResponse

router = APIRouter(tags=["auth"])


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse
)
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


@router.post("/token")
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
        verify_password(form_data.password, DUMMY_HASH)
        raise credentials_exception

    if not verify_password(form_data.password, existing_user.hashed_password):
        raise credentials_exception

    data = {"sub": existing_user.email, "sid": str(uuid4()), "scopes": form_data.scopes}
    access_token = create_access_token(data=data)
    refresh_token = create_refresh_token(data=data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/token/refresh")
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

    new_access_token = create_access_token(data={"sub": user.email, "sid": session_id})
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(
    session: SessionDep,
    current_user: CurrentUser,
    payload: AccessTokenPayload,
):
    session_id = payload["sid"]
    if payload["sub"] != current_user.email:
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
