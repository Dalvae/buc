import uuid
from typing import List, Optional

from fastapi import HTTPException
from sqlmodel import Session, select, func

from app.models import Company, CompanyCreate, CompanyUpdate, User, UserRole


def get(*, session: Session, company_id: uuid.UUID) -> Optional[Company]:
    return session.get(Company, company_id)


def get_multi(*, session: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[Company]:
    if current_user.is_superuser or current_user.role == UserRole.ADMIN:
        statement = select(Company).offset(skip).limit(limit)
        return list(session.exec(statement).all())
    if current_user.company_id:
        statement = select(Company).where(Company.id == current_user.company_id)
        company = session.exec(statement).first()
        return [company] if company else []
    return []


def count(*, session: Session, current_user: User) -> int:
    if current_user.is_superuser or current_user.role == UserRole.ADMIN:
        count_statement = select(func.count()).select_from(Company)
    elif current_user.company_id:
        count_statement = select(func.count(Company.id)).where(Company.id == current_user.company_id)
    else:
        return 0
    count = session.exec(count_statement).one_or_none()
    return count if count is not None else 0


def create(*, session: Session, company_in: CompanyCreate) -> Company:
    db_company = Company.model_validate(company_in)
    session.add(db_company)
    session.flush()
    session.refresh(db_company)
    return db_company


def update(*, session: Session, db_company: Company, company_in: CompanyUpdate) -> Company:
    company_data = company_in.model_dump(exclude_unset=True)
    db_company.sqlmodel_update(company_data)
    session.add(db_company)
    session.flush()
    session.refresh(db_company)
    return db_company


def remove(*, session: Session, company_id: uuid.UUID) -> Optional[Company]:
    company = session.get(Company, company_id)
    if not company:
        return None
    session.delete(company)
    session.flush()
    return company

class CRUDCompany:
    def get(self, session: Session, *, company_id: uuid.UUID) -> Optional[Company]:
        return get(session=session, company_id=company_id)

    def get_multi(self, session: Session, *, current_user: User, skip: int = 0, limit: int = 100) -> List[Company]:
        return get_multi(session=session, current_user=current_user, skip=skip, limit=limit)

    def count(self, session: Session, *, current_user: User) -> int:
        return count(session=session, current_user=current_user)

    def create(self, session: Session, *, company_in: CompanyCreate) -> Company:
        return create(session=session, company_in=company_in)

    def update(self, session: Session, *, db_company: Company, company_in: CompanyUpdate) -> Company:
        return update(session=session, db_company=db_company, company_in=company_in)

    def remove(self, session: Session, *, company_id: uuid.UUID) -> Optional[Company]:
        return remove(session=session, company_id=company_id)

company = CRUDCompany()