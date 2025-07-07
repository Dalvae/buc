import pytest
from sqlmodel import Session

from app import crud
from app.models import Company, CompanyCreate, CompanyUpdate, User, UserCreate, UserRole
from app.tests.utils.utils import random_email, random_lower_string


@pytest.fixture(name="test_superuser")
def test_superuser_fixture(db: Session) -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = crud.user.create(session=db, user_create=user_in)
    return user


def test_create_company(db: Session, test_superuser: UserCreate) -> None:
    name = random_lower_string()
    company_in = CompanyCreate(name=name, details="Test Company Details")
    company = crud.company.create(session=db, company_in=company_in)
    assert company.name == name
    assert company.details == "Test Company Details"


def test_get_company(db: Session, test_superuser: UserCreate) -> None:
    name = random_lower_string()
    company_in = CompanyCreate(name=name, details="Test Company Details")
    company = crud.company.create(session=db, company_in=company_in)
    assert company.id is not None
    fetched_company = crud.company.get(session=db, company_id=company.id)
    assert fetched_company
    assert fetched_company.name == name


def test_get_companies_as_superuser(db: Session, test_superuser: User) -> None:
    company_in1 = CompanyCreate(name=random_lower_string(), details="Details 1")
    crud.company.create(session=db, company_in=company_in1)
    company_in2 = CompanyCreate(name=random_lower_string(), details="Details 2")
    crud.company.create(session=db, company_in=company_in2)

    companies = crud.company.get_multi(session=db, current_user=test_superuser)
    assert len(companies) >= 2 # May have other companies from other tests


def test_get_companies_as_admin(db: Session, test_superuser: UserCreate) -> None:
    admin_user_in = UserCreate(email=random_email(), password=random_lower_string(), role=UserRole.ADMIN)
    admin_user = crud.user.create(session=db, user_create=admin_user_in)

    company_in1 = CompanyCreate(name=random_lower_string(), details="Details 1")
    crud.company.create(session=db, company_in=company_in1)
    company_in2 = CompanyCreate(name=random_lower_string(), details="Details 2")
    crud.company.create(session=db, company_in=company_in2)

    companies = crud.company.get_multi(session=db, current_user=admin_user)
    assert len(companies) >= 2


def test_get_companies_as_normal_user(db: Session, test_superuser: UserCreate) -> None:
    company_in = CompanyCreate(name=random_lower_string(), details="User Company")
    user_company = crud.company.create(session=db, company_in=company_in)

    normal_user_in = UserCreate(email=random_email(), password=random_lower_string(), company_id=user_company.id, role=UserRole.USER)
    normal_user = crud.user.create(session=db, user_create=normal_user_in)

    companies = crud.company.get_multi(session=db, current_user=normal_user)
    assert len(companies) == 1
    assert companies[0].id == user_company.id


def test_update_company(db: Session, test_superuser: UserCreate) -> None:
    name = random_lower_string()
    company_in = CompanyCreate(name=name, details="Test Company Details")
    company = crud.company.create(session=db, company_in=company_in)

    new_name = random_lower_string()
    company_update_in = CompanyUpdate(name=new_name, details="Updated Details")
    updated_company = crud.company.update(session=db, db_company=company, company_in=company_update_in)

    assert updated_company.name == new_name
    assert updated_company.details == "Updated Details"


def test_delete_company(db: Session, test_superuser: UserCreate) -> None:
    name = random_lower_string()
    company_in = CompanyCreate(name=name, details="Test Company Details")
    company = crud.company.create(session=db, company_in=company_in)

    assert company.id is not None
    deleted_company = crud.company.remove(session=db, company_id=company.id)
    assert deleted_company is not None
    assert deleted_company.id == company.id

    fetched_company = crud.company.get(session=db, company_id=company.id)
    assert fetched_company is None
