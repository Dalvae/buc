import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.models import Area, AreaCreate, Company, CompanyCreate, User, UserCreate, UserRole, UserAreaAssignmentLink
from app.tests.utils.utils import random_email, random_lower_string


@pytest.fixture(name="test_superuser_and_company")
def test_superuser_and_company_fixture(db: Session) -> tuple[User, Company]:
    superuser_in = UserCreate(email=random_email(), password=random_lower_string(), is_superuser=True)
    superuser = crud.user.create(session=db, user_create=superuser_in)
    company_in = CompanyCreate(name=random_lower_string(), details="Initial Company")
    company = crud.company.create(session=db, company_in=company_in)
    return superuser, company


@pytest.fixture(name="test_area")
def test_area_fixture(db: Session, test_superuser_and_company: tuple[User, Company]) -> Area:
    superuser, company = test_superuser_and_company
    area_in = AreaCreate(name=random_lower_string(), description="Test Area Description")
    assert company.id is not None
    area = crud.area.create(session=db, area_in=area_in, company_id=company.id)
    return area


@pytest.fixture(name="normal_user_in_company")
def normal_user_in_company_fixture(db: Session, test_superuser_and_company: tuple[User, Company]) -> User:
    superuser, company = test_superuser_and_company
    user_in = UserCreate(email=random_email(), password=random_lower_string(), company_id=company.id, role=UserRole.USER)
    user = crud.user.create(session=db, user_create=user_in)
    return user


@pytest.fixture(name="auditor_user_in_company")
def auditor_user_in_company_fixture(db: Session, test_superuser_and_company: tuple[User, Company]) -> User:
    superuser, company = test_superuser_and_company
    assert company.id is not None
    user_in = UserCreate(email=random_email(), password=random_lower_string(), company_id=company.id, role=UserRole.AUDITOR)
    user = crud.user.create(session=db, user_create=user_in)
    return user


def test_create_area(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_superuser_and_company: tuple[User, Company],
) -> None:
    superuser, company = test_superuser_and_company
    name = random_lower_string()
    data = {"name": name, "description": "A new test area"}
    response = client.post(
        f"/api/v1/companies/{company.id}/areas/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == name
    assert content["description"] == "A new test area"
    assert "id" in content
    assert content["company_id"] == str(company.id)

    area_in_db = db.get(Area, uuid.UUID(content["id"]))
    assert area_in_db
    assert area_in_db.name == name


def test_create_area_duplicate_name(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_superuser_and_company: tuple[User, Company],
) -> None:
    superuser, company = test_superuser_and_company
    name = random_lower_string()
    area_in = AreaCreate(name=name, description="Existing Area")
    crud.area.create(session=db, area_in=area_in, company_id=company.id)

    data = {"name": name, "description": "Another area with same name"}
    response = client.post(
        f"/api/v1/companies/{company.id}/areas/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 409


def test_read_areas_as_superuser(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_superuser_and_company: tuple[User, Company],
) -> None:
    superuser, company = test_superuser_and_company
    area_in1 = AreaCreate(name=random_lower_string(), description="Area 1")
    crud.area.create(session=db, area_in=area_in1, company_id=company.id)
    area_in2 = AreaCreate(name=random_lower_string(), description="Area 2")
    crud.area.create(session=db, area_in=area_in2, company_id=company.id)

    response = client.get(
        f"/api/v1/companies/{company.id}/areas/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2
    assert any(a["name"] == area_in1.name for a in content["data"])


def test_read_areas_as_normal_user_in_company(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
    test_superuser_and_company: tuple[User, Company],
    normal_user_in_company: User,
) -> None:
    superuser, company = test_superuser_and_company
    area_in1 = AreaCreate(name=random_lower_string(), description="Area 1")
    area1 = crud.area.create(session=db, area_in=area_in1, company_id=company.id)
    area_in2 = AreaCreate(name=random_lower_string(), description="Area 2")
    area2 = crud.area.create(session=db, area_in=area_in2, company_id=company.id)

    # Assign user to area1
    link = UserAreaAssignmentLink(user_id=normal_user_in_company.id, area_id=area1.id)
    db.add(link)
    db.commit()
    db.refresh(normal_user_in_company)

    response = client.get(
        f"/api/v1/companies/{company.id}/areas/",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    # Currently, get_areas_by_company_db for non-admin/superuser returns all areas in company if user belongs to company.
    # This test reflects that current behavior. If granular area access is implemented, this test needs adjustment.
    assert len(content["data"]) >= 2
    assert any(a["name"] == area_in1.name for a in content["data"])


def test_read_areas_as_normal_user_not_in_company(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
    test_superuser_and_company: tuple[User, Company],
) -> None:
    superuser, company = test_superuser_and_company
    # Create another company not associated with the normal user
    other_company_in = CompanyCreate(name=random_lower_string(), details="Other Company")
    other_company = crud.company.create(session=db, company_in=other_company_in)

    response = client.get(
        f"/api/v1/companies/{other_company.id}/areas/",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403 # Should not have access


def test_read_area_by_id_as_superuser(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_area: Area,
) -> None:
    response = client.get(
        f"/api/v1/companies/{test_area.company_id}/areas/{test_area.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(test_area.id)
    assert content["name"] == test_area.name


def test_read_area_by_id_as_normal_user_with_access(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
    normal_user_in_company: User,
    test_area: Area,
) -> None:
    # Assign user to area
    link = UserAreaAssignmentLink(user_id=normal_user_in_company.id, area_id=test_area.id)
    db.add(link)
    db.commit()
    db.refresh(normal_user_in_company)

    response = client.get(
        f"/api/v1/companies/{test_area.company_id}/areas/{test_area.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(test_area.id)


def test_read_area_by_id_as_normal_user_without_access(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
    normal_user_in_company: User,
    test_superuser_and_company: tuple[User, Company],
) -> None:
    superuser, company = test_superuser_and_company
    # Create an area that the normal user is not assigned to
    unassigned_area_in = AreaCreate(name=random_lower_string(), description="Unassigned Area")
    unassigned_area = crud.area.create(session=db, area_in=unassigned_area_in, company_id=company.id)

    response = client.get(
        f"/api/v1/companies/{company.id}/areas/{unassigned_area.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403 # Should not have access


def test_update_area(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_area: Area,
) -> None:
    new_name = random_lower_string()
    data = {"name": new_name, "description": "Updated description"}
    response = client.patch(
        f"/api/v1/companies/{test_area.company_id}/areas/{test_area.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == new_name
    assert content["description"] == "Updated description"

    area_in_db = db.get(Area, test_area.id)
    assert area_in_db
    assert area_in_db.name == new_name


def test_delete_area(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_area: Area,
) -> None:
    company_id = test_area.company_id
    area_id = test_area.id
    response = client.delete(
        f"/api/v1/companies/{company_id}/areas/{area_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Area deleted successfully"

    area_in_db = db.get(Area, area_id)
    assert area_in_db is None


def test_delete_area_not_found(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.delete(
        f"/api/v1/companies/{uuid.uuid4()}/areas/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Area not found or does not belong to this company"


def test_delete_area_with_assigned_users(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_area: Area,
    normal_user_in_company: User,
) -> None:
    # Assign a user to the area
    link = UserAreaAssignmentLink(user_id=normal_user_in_company.id, area_id=test_area.id)
    db.add(link)
    db.commit()

    response = client.delete(
        f"/api/v1/companies/{test_area.company_id}/areas/{test_area.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 400
    assert "Cannot delete area with associated audit assignments or user assignments" in response.json()["detail"]
