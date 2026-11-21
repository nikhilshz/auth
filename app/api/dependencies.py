from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import select

from app.core.security import decode_token
from app.db.session import SessionDep
from app.models import RevokedSession, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def _invalid_token_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_access_token_payload(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict:
    payload = decode_token(token)
    if (
        not payload
        or payload.get("type") != "access"
        or not payload.get("sid")
        or not payload.get("sub")
    ):
        raise _invalid_token_exception()

    return payload


AccessTokenPayload = Annotated[dict, Depends(get_access_token_payload)]


def get_current_user(session: SessionDep, payload: AccessTokenPayload):

    session_id = payload["sid"]
    if not session_id or session.get(RevokedSession, session_id):
        raise _invalid_token_exception()

    email = payload["sub"]
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise _invalid_token_exception()

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

Role = Literal["user", "admin"]


class RoleRequired:
    def __init__(self, role: Role):
        self.role = role

    def __call__(self, current_user: CurrentUser):
        if current_user.role != self.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires the '{self.role}' role",
            )
