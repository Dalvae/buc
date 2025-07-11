from typing import Any

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.core.security import get_password_hash
from app.models import (
    PrivateUserCreate,
    User,
    UserPublic,
)

router = APIRouter(tags=["private"], prefix="/private")


@router.post("/users/", response_model=UserPublic)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> Any:
    """
    Create a new user.
    """

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        is_verified=user_in.is_verified,
    )

    session.add(user)
    session.commit()

    return user
