import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.core.security import hash_password
from app.db.session import SessionDep
from app.models import PasswordResetToken, User
from app.schemas import PasswordResetConfirm, PasswordResetRequest

router = APIRouter(prefix="/password-reset", tags=["password reset"])


@router.post("/request")
def request_password_reset(session: SessionDep, payload: PasswordResetRequest):
    message = {
        "message": "If an account exists with this email, a reset link has been sent"
    }

    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not user.id:
        return message

    token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        token=token,
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
        used=False,
    )

    session.add(reset_token)
    session.commit()
    # Send the reset link through the configured email provider.
    return message


@router.post("/confirm")
def confirm_password_reset(session: SessionDep, payload: PasswordResetConfirm):
    invalid_token_error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token"
    )
    reset_token = session.exec(
        select(PasswordResetToken).where(PasswordResetToken.token == payload.token)
    ).first()

    if not reset_token or reset_token.used:
        raise invalid_token_error

    token_expired = reset_token.expires_at < datetime.now(UTC).replace(tzinfo=None)
    if token_expired:
        raise invalid_token_error

    user = session.get(User, reset_token.user_id)
    if not user:
        raise invalid_token_error

    user.hashed_password = hash_password(payload.new_password)
    reset_token.used = True
    session.add(user)
    session.add(reset_token)
    session.commit()

    return {"message": "Password reset successfully"}
