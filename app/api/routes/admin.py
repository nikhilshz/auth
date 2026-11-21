from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.api.dependencies import RoleRequired
from app.db.session import SessionDep
from app.models import User
from app.schemas import UserResponse

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(RoleRequired("admin"))]
)


@router.get("/users", response_model=list[UserResponse])
def get_all_users(session: SessionDep):
    return session.exec(select(User)).all()


@router.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(session: SessionDep, user_id: int):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    session.delete(user)
    session.commit()

    return user
