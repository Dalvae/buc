import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import col, delete, func, select

from app.crud.user import user as crud_user
from app.api.deps import (
    CurrentActiveAdminOrSuperuser,
    CurrentActiveUser,
    SessionDep,
    obfuscate_data_for_demo_company,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import (
    Area,
    Message,
    UpdatePassword,
    User,
    UserAreaAssignmentLink,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
    UserRole,
)
from app.utils import generate_new_account_email, send_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    response_model=UsersPublic,
)
def read_users(session: SessionDep, current_user: CurrentActiveAdminOrSuperuser, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    users_db = session.exec(statement).all()

    users_db = obfuscate_data_for_demo_company(users_db, current_user)

    return UsersPublic(data=users_db, count=count)


@router.post(
    "/", response_model=UserPublic
)
def create_user(*, session: SessionDep, user_in: UserCreate, current_user: CurrentActiveAdminOrSuperuser) -> Any:
    """
    Create new user.
    """
    user = crud_user.get_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = crud_user.create(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    
    user = obfuscate_data_for_demo_company(user, current_user)
    return user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentActiveUser
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = crud_user.get_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    current_user = obfuscate_data_for_demo_company(current_user, current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentActiveUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentActiveUser) -> Any:
    """
    Get current user.
    """
    current_user = obfuscate_data_for_demo_company(current_user, current_user)
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentActiveUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_new_user(
    *,
    session: SessionDep,
    user_in: UserRegister,
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = crud_user.get_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = crud_user.create(session=session, user_create=user_create)

    user = obfuscate_data_for_demo_company(user, user) # Obfuscate for the user themselves
    return user


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentActiveUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id != current_user.id and not (current_user.is_superuser or current_user.role == UserRole.ADMIN):
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    
    user = obfuscate_data_for_demo_company(user, current_user)
    return user


@router.patch(
    "/{user_id}",
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
    current_user: CurrentActiveAdminOrSuperuser,
) -> Any:
    """
    Update a user.
    """

    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = crud_user.get_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = crud_user.update(session=session, db_user=db_user, user_in=user_in)
    
    db_user = obfuscate_data_for_demo_company(db_user, current_user)
    return db_user


@router.delete("/{user_id}")
def delete_user(
    session: SessionDep, current_user: CurrentActiveAdminOrSuperuser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post(
    "/{user_id}/assign-areas",
    response_model=UserPublic,
)
def assign_user_to_areas(
    user_id: uuid.UUID,
    area_ids: List[uuid.UUID],
    session: SessionDep,
    current_user: CurrentActiveAdminOrSuperuser,
) -> Any:
    """
    Assign a user to multiple areas. This will overwrite existing assignments.
    The areas must belong to the user's primary company.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.company_id:
        raise HTTPException(status_code=400, detail="User must have a primary company assigned before assigning areas.")

    # Clear existing assignments for this user
    session.execute(delete(UserAreaAssignmentLink).where(col(UserAreaAssignmentLink.user_id) == user_id))
    session.commit()

    new_assignments = []
    for area_id in area_ids:
        area = session.get(Area, area_id)
        if not area or area.company_id != user.company_id:
            raise HTTPException(
                status_code=400,
                detail=f"Area {area_id} not found or does not belong to user's company {user.company_id}"
            )
        link = UserAreaAssignmentLink(user_id=user_id, area_id=area_id)
        session.add(link)
        new_assignments.append(link)
    
    session.commit()
    session.refresh(user)
    # Refresh relationships to ensure assigned_areas is updated
    session.refresh(user, attribute_names=["assigned_areas"])

    is_in_demo_company = user.company.is_demo if user.company else False
    return UserPublic.model_validate(
        user,
        context={"viewer_role": current_user.role, "is_user_in_demo_company": is_in_demo_company}
    )


@router.delete(
    "/{user_id}/remove-area/{area_id}",
    response_model=Message,
)
def remove_user_from_area(
    user_id: uuid.UUID,
    area_id: uuid.UUID,
    session: SessionDep,
) -> Message:
    """
    Remove a user's assignment from a specific area.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    link_statement = select(UserAreaAssignmentLink).where(
        UserAreaAssignmentLink.user_id == user_id,
        UserAreaAssignmentLink.area_id == area_id,
    )
    link = session.exec(link_statement).first()

    if not link:
        raise HTTPException(status_code=404, detail="User is not assigned to this area.")

    session.delete(link)
    session.commit()
    return Message(message="User successfully removed from area.")
