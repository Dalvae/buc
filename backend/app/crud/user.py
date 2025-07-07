
import uuid
from typing import Any, Dict, Optional, Union

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import User, UserCreate, UserUpdate


def get_by_email(*, session: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def create(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.flush()
    session.refresh(db_obj)
    return db_obj


def update(*, session: Session, db_user: User, user_in: Union[UserUpdate, Dict[str, Any]]) -> User:
    if isinstance(user_in, dict):
        update_data = user_in
    else:
        update_data = user_in.model_dump(exclude_unset=True)

    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password

    db_user.sqlmodel_update(update_data)
    session.add(db_user)
    session.flush()
    session.refresh(db_user)
    return db_user


def authenticate(*, session: Session, email: str, password: str) -> Optional[User]:
    db_user = get_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user

class CRUDUser:
    def get_by_email(self, session: Session, *, email: str) -> Optional[User]:
        return get_by_email(session=session, email=email)

    def create(self, session: Session, *, user_create: UserCreate) -> User:
        return create(session=session, user_create=user_create)

    def update(
        self, session: Session, *, db_user: User, user_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        return update(session=session, db_user=db_user, user_in=user_in)

    def authenticate(self, session: Session, *, email: str, password: str) -> Optional[User]:
        return authenticate(session=session, email=email, password=password)

user = CRUDUser()
