from collections.abc import Generator
from typing import Annotated, Any
import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session, select

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import TokenPayload, User, UserRole, Company, Area, UserAreaAssignmentLink, AuditResponse

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_user(current_user: CurrentUser) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]


def get_current_active_admin_or_superuser(current_user: CurrentActiveUser) -> User:
    if not (current_user.is_superuser or current_user.role == UserRole.ADMIN):
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


CurrentActiveAdminOrSuperuser = Annotated[User, Depends(get_current_active_admin_or_superuser)]


def get_current_active_auditor(current_user: CurrentActiveUser) -> User:
    if current_user.role != UserRole.AUDITOR:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges (Auditor role required)"
        )
    return current_user


CurrentActiveAuditor = Annotated[User, Depends(get_current_active_auditor)]


def get_current_active_user_with_company_access(
    company_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentActiveUser,
) -> User:
    if current_user.is_superuser or current_user.role == UserRole.ADMIN:
        return current_user

    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not enough permissions to access this company")
    
    return current_user


CurrentActiveUserWithCompanyAccess = Annotated[User, Depends(get_current_active_user_with_company_access)]


def get_current_active_user_with_area_access(
    area_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentActiveUser,
) -> User:
    if current_user.is_superuser or current_user.role == UserRole.ADMIN:
        return current_user

    area = session.get(Area, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")

    # Check if the user's primary company matches the area's company
    if current_user.company_id != area.company_id:
        raise HTTPException(status_code=403, detail="Not enough permissions to access this area (company mismatch)")

    # Check if the user is explicitly assigned to this area
    link = session.exec(
        select(UserAreaAssignmentLink).where(
            UserAreaAssignmentLink.user_id == current_user.id,
            UserAreaAssignmentLink.area_id == area_id,
        )
    ).first()
    if not link:
        raise HTTPException(status_code=403, detail="Not enough permissions to access this area (not assigned)")
    
    return current_user


CurrentActiveUserWithAreaAccess = Annotated[User, Depends(get_current_active_user_with_area_access)]

def obfuscate_data_for_demo_company(data: Any, current_user: User) -> Any:
    is_viewer_privileged = current_user.is_superuser or current_user.role == UserRole.ADMIN
    if is_viewer_privileged:
        return data

    was_list = isinstance(data, list)
    items = data if was_list else [data]
    
    # We create copies to avoid mutating session-managed objects
    copied_items = [item.model_copy(deep=True) for item in items]

    for item in copied_items:
        company = None
        # This can trigger lazy-loading if relationships are not pre-loaded.
        # Ensure your CRUD functions load necessary relationships for performance.
        if hasattr(item, 'company') and item.company:
            company = item.company
        elif hasattr(item, 'audit_assignment') and item.audit_assignment and hasattr(item.audit_assignment, 'company'):
            company = item.audit_assignment.company

        if company and company.is_demo:
            if hasattr(item, 'email'):
                item.email = "hidden"
            if hasattr(item, 'full_name'):
                item.full_name = "Demo User"
            # Special handling for AuditResponse auditor details
            if isinstance(item, AuditResponse) and hasattr(item, 'auditor') and item.auditor:
                item.auditor.email = "hidden"
                item.auditor.full_name = "Demo User"
                
    return copied_items if was_list else copied_items[0]
