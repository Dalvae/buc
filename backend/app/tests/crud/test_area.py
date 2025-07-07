import pytest
from sqlmodel import Session, select
from uuid import UUID

from app import crud
from fastapi import HTTPException
from app.models import Area, Company, User, UserRole, UserAreaAssignmentLink, CompanyCreate, UserCreate, AreaCreate, AreaUpdate
from app.tests.utils.utils import random_email, random_lower_string

@pytest.fixture(name="test_company")
def test_company_fixture(db: Session) -> Company:
    company_in = CompanyCreate(name=random_lower_string(), details="Test Company Details")
    company = crud.company.create(session=db, company_in=company_in)
    return company


def test_create_area(db: Session, test_company: Company) -> None:
    assert test_company.id is not None
    name = random_lower_string()
    area_in = AreaCreate(name=name, description="Test Area Description")
    area = crud.area.create(session=db, area_in=area_in, company_id=test_company.id)
    assert area.name == name
    assert area.description == "Test Area Description"
    assert area.company_id == test_company.id

    if area.id:
        fetched_area = crud.area.get(session=db, area_id=area.id)
        assert fetched_area is not None
        assert fetched_area.name == name


def test_create_area_duplicate_name(db: Session, test_company: Company) -> None:
    assert test_company.id is not None
    name = random_lower_string()
    area_in = AreaCreate(name=name, description="Existing Area")
    crud.area.create(session=db, area_in=area_in, company_id=test_company.id)

    with pytest.raises(HTTPException):
        crud.area.create(session=db, area_in=area_in, company_id=test_company.id)


def test_read_areas_as_superuser(db: Session, test_company: Company, superuser: User) -> None:
    assert test_company.id is not None
    area_in1 = AreaCreate(name=random_lower_string(), description="Area 1")
    crud.area.create(session=db, area_in=area_in1, company_id=test_company.id)
    area_in2 = AreaCreate(name=random_lower_string(), description="Area 2")
    crud.area.create(session=db, area_in=area_in2, company_id=test_company.id)

    areas = crud.area.get_multi_by_company(session=db, company_id=test_company.id, current_user=superuser)
    assert len(areas) >= 2
    assert any(a.name == area_in1.name for a in areas)


def test_read_areas_as_normal_user_in_company(db: Session, test_company: Company, normal_user_in_company: User) -> None:
    assert test_company.id is not None
    area_in1 = AreaCreate(name=random_lower_string(), description="Area 1")
    crud.area.create(session=db, area_in=area_in1, company_id=test_company.id)
    area_in2 = AreaCreate(name=random_lower_string(), description="Area 2")
    crud.area.create(session=db, area_in=area_in2, company_id=test_company.id)

    areas = crud.area.get_multi_by_company(session=db, company_id=test_company.id, current_user=normal_user_in_company)
    assert len(areas) >= 2
    assert any(a.name == area_in1.name for a in areas)


def test_read_area_by_id_as_superuser(db: Session, test_company: Company, test_area: Area) -> None:
    assert test_area.id is not None
    response = crud.area.get(session=db, area_id=test_area.id)
    assert response is not None
    assert response.name == test_area.name


def test_read_area_by_id_as_normal_user_with_access(db: Session, normal_user_in_company: User, test_area: Area) -> None:
    # Assign user to area
    assert normal_user_in_company.id is not None
    assert test_area.id is not None
    link = UserAreaAssignmentLink(user_id=normal_user_in_company.id, area_id=test_area.id)
    db.add(link)
    db.commit()
    db.refresh(normal_user_in_company)
    response = crud.area.get(session=db, area_id=test_area.id)
    assert response is not None


def test_read_area_by_id_as_normal_user_without_access(db: Session, normal_user_in_company: User, test_company: Company, test_area: Area) -> None:
    assert test_company.id is not None
    # Create an area that the normal user is not assigned to
    unassigned_area_in = AreaCreate(name=random_lower_string(), description="Unassigned Area")
    unassigned_area = crud.area.create(session=db, area_in=unassigned_area_in, company_id=test_company.id)

    assert unassigned_area.id is not None
    response = crud.area.get(session=db, area_id=unassigned_area.id)
    assert response is None


def test_update_area(db: Session, test_company: Company, test_area: Area) -> None:
    assert test_area.id is not None
    new_name = random_lower_string()
    area_update_in = AreaUpdate(name=new_name, description="Updated description")
    updated_area = crud.area.update(session=db, db_area=test_area, area_in=area_update_in)
    assert updated_area.name == new_name
    assert updated_area.description == "Updated description"
    assert updated_area.id == test_area.id


def test_update_area_duplicate_name_in_same_company(db: Session, test_company: Company, test_area: Area) -> None:
    assert test_company.id is not None
    name1 = random_lower_string()
    name2 = random_lower_string()
    area_in1 = AreaCreate(name=name1, description="Area 1")
    area1 = crud.area.create(session=db, area_in=area_in1, company_id=test_company.id)
    area_in2 = AreaCreate(name=name2, description="Area 2")
    area2 = crud.area.create(session=db, area_in=area_in2, company_id=test_company.id)

    area_update_in = AreaUpdate(name=name1)  # Try to rename area2 to name1
    with pytest.raises(HTTPException):
        crud.area.update(session=db, db_area=area2, area_in=area_update_in)


def test_delete_area(db: Session, test_company: Company, test_area: Area) -> None:
    assert test_area.id is not None
    assert test_company.id is not None
    response = crud.area.remove(session=db, area_id=test_area.id, company_id=test_company.id)
    assert response is not None
    assert response.id == test_area.id

    fetched_area = crud.area.get(session=db, area_id=test_area.id)
    assert fetched_area is None



