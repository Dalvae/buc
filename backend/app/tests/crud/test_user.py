import pytest
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlmodel import Session

from app import crud
from app.core.security import verify_password
from app.models import Company, CompanyCreate, User, UserCreate, UserUpdate, UserRole
from app.tests.utils.utils import random_email, random_lower_string


@pytest.fixture(name="test_company")
def test_company_fixture(db: Session) -> Company:
    company_in = CompanyCreate(name=random_lower_string(), details="Test Company Details")
    # Create a superuser to create the company
    superuser_in = UserCreate(email=random_email(), password=random_lower_string(), is_superuser=True)
    superuser = crud.user.create(session=db, user_create=superuser_in)
    company = crud.company.create(session=db, company_in=company_in)
    db.commit()
    return company


def test_create_user(db: Session, test_company: Company) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, company_id=test_company.id, role=UserRole.USER)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()
    assert user.email == email
    assert hasattr(user, "hashed_password")
    assert user.role == UserRole.USER
    assert user.company_id == test_company.id
    assert user.is_verified is False # Default value

def test_create_user_without_company_for_user_role_fails(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    with pytest.raises(ValidationError) as excinfo:
        UserCreate(email=email, password=password, role=UserRole.USER)
    assert "company_id is required for USER and AUDITOR roles" in str(excinfo.value)

def test_create_user_without_company_for_auditor_role_fails(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    with pytest.raises(ValidationError) as excinfo:
        UserCreate(email=email, password=password, role=UserRole.AUDITOR)
    assert "company_id is required for USER and AUDITOR roles" in str(excinfo.value)

def test_create_admin_user_without_company_succeeds(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, role=UserRole.ADMIN)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()
    assert user.email == email
    assert user.role == UserRole.ADMIN
    assert user.company_id is None # Admins don't strictly need a company_id

def test_authenticate_user(db: Session, test_company: Company) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, company_id=test_company.id, role=UserRole.USER)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()
    authenticated_user = crud.user.authenticate(session=db, email=email, password=password)
    assert authenticated_user
    assert user.email == authenticated_user.email


def test_not_authenticate_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = crud.user.authenticate(session=db, email=email, password=password)
    assert user is None


def test_check_if_user_is_active(db: Session, test_company: Company) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_active=True, company_id=test_company.id, role=UserRole.USER)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()
    assert user.is_active is True


def test_check_if_user_is_active_inactive(db: Session, test_company: Company) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_active=False, company_id=test_company.id, role=UserRole.USER)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()
    assert user.is_active is False


def test_check_if_user_is_superuser(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()
    assert user.is_superuser is True


def test_check_if_user_is_superuser_normal_user(db: Session, test_company: Company) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password, company_id=test_company.id, role=UserRole.USER)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()
    assert user.is_superuser is False


def test_get_user(db: Session, test_company: Company) -> None:
    password = random_lower_string()
    username = random_email()
    user_in = UserCreate(email=username, password=password, is_superuser=True)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()
    user_2 = db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


def test_update_user(db: Session, test_company: Company) -> None:
    password = random_lower_string()
    email = random_email()
    user_in = UserCreate(email=email, password=password, company_id=test_company.id, role=UserRole.USER)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()
    new_password = random_lower_string()
    new_full_name = random_lower_string()
    user_in_update = UserUpdate(password=new_password, full_name=new_full_name, is_verified=True)
    if user.id is not None:
        updated_user = crud.user.update(session=db, db_user=user, user_in=user_in_update)
        db.commit()
    user_2 = db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    assert verify_password(new_password, user_2.hashed_password)
    assert updated_user.full_name == new_full_name
    assert updated_user.is_verified is True
