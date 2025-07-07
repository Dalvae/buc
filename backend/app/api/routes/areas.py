import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.crud.area import area as crud_area
from app.api.deps import (
    CurrentActiveAdminOrSuperuser,
    SessionDep,
    get_current_active_user_with_area_access,
    get_current_active_user_with_company_access,
)
from app.models import AreaCreate, AreaPublic, AreaUpdate, AreasPublic, Message, User

router = APIRouter(prefix="/companies/{company_id}/areas", tags=["areas"])


@router.get(
    "/",
    response_model=AreasPublic,
)
def read_areas(
    company_id: uuid.UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user_with_company_access),  # noqa: ARG001
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve areas for a specific company.
    """
    areas = crud_area.get_multi_by_company(session=session, company_id=company_id, current_user=current_user, skip=skip, limit=limit)
    count = crud_area.count_by_company(session=session, company_id=company_id, current_user=current_user)
    return AreasPublic(data=areas, count=count)


@router.post(
    "/",
    response_model=AreaPublic,
)
def create_area(
    company_id: uuid.UUID,
    *, session: SessionDep,
    area_in: AreaCreate,
    current_user: CurrentActiveAdminOrSuperuser,  # noqa: ARG001
) -> Any:
    """
    Create new area within a company.
    """
    area = crud_area.create(session=session, area_in=area_in, company_id=company_id)
    return area


@router.get(
    "/{area_id}",
    response_model=AreaPublic,
)
def read_area_by_id(
    company_id: uuid.UUID,
    area_id: uuid.UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user_with_area_access),  # noqa: ARG001
) -> Any:
    """
    Get a specific area by id.
    """
    area = crud_area.get(session=session, area_id=area_id, company_id=company_id)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found or does not belong to this company")
    return area


@router.patch(
    "/{area_id}",
    response_model=AreaPublic,
)
def update_area(
    company_id: uuid.UUID,
    area_id: uuid.UUID,
    *, session: SessionDep,
    area_in: AreaUpdate,
    current_user: CurrentActiveAdminOrSuperuser,  # noqa: ARG001
) -> Any:
    """
    Update an area.
    """
    area = crud_area.get(session=session, area_id=area_id, company_id=company_id)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found or does not belong to this company")
    
    area = crud_area.update(session=session, db_area=area, area_in=area_in)
    return area


@router.delete(
    "/{area_id}",
    response_model=Message,
)
def delete_area(
    company_id: uuid.UUID,
    area_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentActiveAdminOrSuperuser,  # noqa: ARG001
) -> Message:
    """
    Delete an area.
    """
    area = crud_area.get(session=session, area_id=area_id, company_id=company_id)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found or does not belong to this company")
    
    try:
        crud_area.remove(session=session, area_id=area_id, company_id=company_id)
    except HTTPException as e:
        raise e # Re-raise specific HTTPExceptions from crud
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not delete area: {e}")

    return Message(message="Area deleted successfully")
