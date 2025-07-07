import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select

from app.crud.company import company as crud_company
from app.api.deps import (
    CurrentActiveAdminOrSuperuser,
    CurrentActiveUser,
    SessionDep,
    get_current_active_user_with_company_access,
)
from app.models import Company, CompanyCreate, CompanyPublic, CompaniesPublic, CompanyUpdate, Message, UserRole, User

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get(
    "/",
    response_model=CompaniesPublic,
)
def read_companies(
    session: SessionDep,
    current_user: CurrentActiveUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve companies.
    """
    companies = crud_company.get_multi(session=session, current_user=current_user, skip=skip, limit=limit)
    count = crud_company.count(session=session, current_user=current_user)

    companies_public_data = []
    for company_obj in companies:
        company_public = CompanyPublic.model_validate(
            company_obj,
            context={"viewer_role": current_user.role}
        )
        companies_public_data.append(company_public)

    return CompaniesPublic(data=companies_public_data, count=count)


@router.post(
    "/",
    response_model=CompanyPublic,
)
def create_company(
    *,
    session: SessionDep,
    company_in: CompanyCreate,
    current_user: CurrentActiveAdminOrSuperuser,
) -> Any:
    """
    Create new company.
    """
    company = crud_company.create(session=session, company_in=company_in)
    return CompanyPublic.model_validate(company, context={"viewer_role": current_user.role})


@router.get(
    "/{company_id}",
    response_model=CompanyPublic,
)
def read_company_by_id(
    company_id: uuid.UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user_with_company_access),
) -> Any:
    """
    Get a specific company by id.
    """
    company = crud_company.get(session=session, company_id=company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return CompanyPublic.model_validate(company, context={"viewer_role": current_user.role})


@router.patch(
    "/{company_id}",
    response_model=CompanyPublic,
)
def update_company(
    *,
    session: SessionDep,
    company_id: uuid.UUID,
    company_in: CompanyUpdate,
    current_user: CurrentActiveAdminOrSuperuser,
) -> Any:
    """
    Update a company.
    """
    company = crud_company.get(session=session, company_id=company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company = crud_company.update(session=session, db_company=company, company_in=company_in)
    return CompanyPublic.model_validate(company, context={"viewer_role": current_user.role})


@router.delete(
    "/{company_id}",
    response_model=Message,
)
def delete_company(
    session: SessionDep,
    company_id: uuid.UUID,
) -> Message:
    """
    Delete a company.
    """
    company = crud_company.get(session=session, company_id=company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Add checks for associated users, areas, assignments before deletion if cascade delete is not fully handled by DB
    # For now, relying on DB cascade delete for relationships defined in models.py
    try:
        crud_company.remove(session=session, company_id=company_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not delete company: {e}")

    return Message(message="Company deleted successfully")
