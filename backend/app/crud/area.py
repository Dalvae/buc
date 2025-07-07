import uuid
from typing import List, Optional

from fastapi import HTTPException
from sqlmodel import Session, select, func

from app.models import Area, AreaCreate, AreaUpdate, Company, User, UserRole


def get(*, session: Session, area_id: uuid.UUID, company_id: Optional[uuid.UUID] = None) -> Optional[Area]:
    statement = select(Area).where(Area.id == area_id)
    if company_id:
        statement = statement.where(Area.company_id == company_id)
    return session.exec(statement).first()


def get_by_name_and_company(*, session: Session, name: str, company_id: uuid.UUID) -> Optional[Area]:
    return session.exec(
        select(Area).where(Area.company_id == company_id, Area.name == name)
    ).first()


def get_multi_by_company(
    *, session: Session, company_id: uuid.UUID, current_user: User, skip: int = 0, limit: int = 100
) -> List[Area]:
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if not (current_user.is_superuser or current_user.role == UserRole.ADMIN or current_user.company_id == company_id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if current_user.is_superuser or current_user.role == UserRole.ADMIN:
        statement = select(Area).where(Area.company_id == company_id)
    else:
        assigned_area_ids = {area.id for area in current_user.assigned_areas if area.id}
        statement = select(Area).where(Area.company_id == company_id)
        if assigned_area_ids:
            statement = statement.where(Area.id.in_(list(assigned_area_ids)))

    statement = statement.offset(skip).limit(limit)
    return list(session.exec(statement).all())


def count_by_company(*, session: Session, company_id: uuid.UUID, current_user: User) -> int:
    # Similar permission checks as get_multi_by_company
    if current_user.is_superuser or current_user.role == UserRole.ADMIN:
        statement = select(func.count(Area.id)).where(Area.company_id == company_id)
    else:
        assigned_area_ids = {area.id for area in current_user.assigned_areas if area.id}
        statement = select(func.count(Area.id)).where(Area.company_id == company_id)
        if assigned_area_ids:
            statement = statement.where(Area.id.in_(list(assigned_area_ids)))
    
    count = session.exec(statement).one_or_none()
    return count if count is not None else 0


def create(*, session: Session, area_in: AreaCreate, company_id: uuid.UUID) -> Area:
    if not session.get(Company, company_id):
        raise HTTPException(status_code=404, detail="Company not found")
    if get_by_name_and_company(session=session, name=area_in.name, company_id=company_id):
        raise HTTPException(status_code=409, detail="Area name already exists in this company")

    db_area = Area.model_validate(area_in, update={"company_id": company_id})
    session.add(db_area)
    session.flush()
    session.refresh(db_area)
    return db_area


def update(*, session: Session, db_area: Area, area_in: AreaUpdate) -> Area:
    area_data = area_in.model_dump(exclude_unset=True)
    if "name" in area_data and area_data["name"] != db_area.name:
        if get_by_name_and_company(session=session, name=area_data["name"], company_id=db_area.company_id):
            raise HTTPException(status_code=409, detail="Area name already exists in this company")

    db_area.sqlmodel_update(area_data)
    session.add(db_area)
    session.flush()
    session.refresh(db_area)
    return db_area


def remove(*, session: Session, area_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Area]:
    area = get(session=session, area_id=area_id, company_id=company_id)
    if not area:
        return None
    if area.audit_assignments:
        raise HTTPException(status_code=400, detail="Cannot delete area with associated audit assignments")
    
    session.delete(area)
    session.flush()
    return area

class CRUDArea:
    def get(self, session: Session, *, area_id: uuid.UUID, company_id: Optional[uuid.UUID] = None) -> Optional[Area]:
        return get(session=session, area_id=area_id, company_id=company_id)

    def get_multi_by_company(
        self, session: Session, *, company_id: uuid.UUID, current_user: User, skip: int = 0, limit: int = 100
    ) -> List[Area]:
        return get_multi_by_company(
            session=session, company_id=company_id, current_user=current_user, skip=skip, limit=limit
        )

    def count_by_company(self, session: Session, *, company_id: uuid.UUID, current_user: User) -> int:
        return count_by_company(session=session, company_id=company_id, current_user=current_user)

    def create(self, session: Session, *, area_in: AreaCreate, company_id: uuid.UUID) -> Area:
        return create(session=session, area_in=area_in, company_id=company_id)

    def update(self, session: Session, *, db_area: Area, area_in: AreaUpdate) -> Area:
        return update(session=session, db_area=db_area, area_in=area_in)

    def remove(self, session: Session, *, area_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Area]:
        return remove(session=session, area_id=area_id, company_id=company_id)

area = CRUDArea()
