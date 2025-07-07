import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.models import (
    AuditAssignment,
    AuditAssignmentCreate,
    AuditTemplate,
    Company,
    CompanyCreate,
    AuditTemplateCreate,
    User,
    UserCreate,
    UserRole,
    Area,
    AreaCreate,
    UserAreaAssignmentLink,
)
from app.tests.utils.utils import random_email, random_lower_string


@pytest.fixture(name="test_superuser")
def test_superuser_fixture(db: Session) -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = crud.user.create(session=db, user_create=user_in)
    return user


@pytest.fixture(name="test_company")
def test_company_fixture(db: Session, test_superuser: User) -> Company:
    company_in = CompanyCreate(name=random_lower_string(), details="Test Company Details")
    company = crud.company.create(session=db, company_in=company_in)
    return company


@pytest.fixture(name="test_area")
def test_area_fixture(db: Session, test_company: Company) -> Area:
    assert test_company.id is not None
    area_in = AreaCreate(name=random_lower_string(), description="Test Area Description")
    area = crud.area.create(session=db, area_in=area_in, company_id=test_company.id)
    return area


@pytest.fixture(name="test_audit_template")
def test_audit_template_fixture(db: Session, test_superuser: User) -> AuditTemplate:
    template_in = AuditTemplateCreate(
        name=random_lower_string(),
        description="Test Audit Template",
        audit_type_definition_key="FIVE_S_AUDIT",
    )
    template = crud.audit_template.create(session=db, template_in=template_in, creator_id=test_superuser.id)
    return template


@pytest.fixture(name="test_auditor")
def test_auditor_fixture(db: Session, test_company: Company) -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, company_id=test_company.id, role=UserRole.AUDITOR)
    user = crud.user.create(session=db, user_create=user_in)
    return user


@pytest.fixture(name="test_audit_assignment")
def test_audit_assignment_fixture(
    db: Session, test_superuser: User, test_audit_template: AuditTemplate, test_company: Company, test_area: Area
) -> AuditAssignment:
    # Ensure the auditor is assigned to the area for the assignment
    assert test_superuser.id is not None
    link = UserAreaAssignmentLink(user_id=test_superuser.id, area_id=test_area.id)
    db.add(link)
    db.commit()
    db.refresh(test_superuser)

    assignment_in = AuditAssignmentCreate(
        audit_template_id=test_audit_template.id,
        company_id=test_company.id,
        area_id=test_area.id,
        title="Test Assignment",
        description="Description for test assignment",
    )
    assignment = crud.audit_assignment.create_with_questions(
        session=db, assignment_in=assignment_in, creator_id=test_superuser.id
    )
    return assignment


def test_create_audit_assignment(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_template: AuditTemplate,
    test_company: Company,
) -> None:
    assert test_company.id is not None
    title = random_lower_string()
    data = {
        "audit_template_id": str(test_audit_template.id),
        "company_id": str(test_company.id),
        "title": title,
        "description": "A new audit assignment",
    }
    response = client.post(
        f"/api/v1/audit-assignments/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == title
    assert content["audit_template_id"] == str(test_audit_template.id)
    assert content["company_id"] == str(test_company.id)
    assert "id" in content
    assert "created_by_id" in content

    assignment_in_db = db.get(AuditAssignment, uuid.UUID(content["id"]))
    assert assignment_in_db
    assert assignment_in_db.title == title
    assert len(assignment_in_db.assigned_questions) > 0  # Should copy questions from template


def test_read_all_audit_assignments_as_superuser(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_assignment: AuditAssignment,
) -> None:
    response = client.get(
        f"/api/v1/audit-assignments/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 1
    assert any(a["id"] == str(test_audit_assignment.id) for a in content["data"])


def test_read_my_audit_assignments_as_auditor(
    client: TestClient,
    auditor_token_headers: dict[str, str],
    db: Session,
    test_audit_assignment: AuditAssignment,
    test_auditor: User,
) -> None:
    # The auditor should be able to see assignments in their company that have no area.
    # The test_auditor and test_audit_assignment are in the same company via fixtures.
    # No need to link to an area since the assignment has no area_id (company-wide)

    response = client.get(
        f"/api/v1/audit-assignments/my-assignments",
        headers=auditor_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 1
    assert any(a["id"] == str(test_audit_assignment.id) for a in content["data"])


def test_read_audit_assignments_for_company(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_assignment: AuditAssignment,
    test_company: Company,
) -> None:
    assert test_company.id is not None
    response = client.get(
        f"/api/v1/audit-assignments/company/{test_company.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 1
    assert any(a["id"] == str(test_audit_assignment.id) for a in content["data"])


def test_read_audit_assignment_by_id(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_assignment: AuditAssignment,
) -> None:
    assert test_audit_assignment.id is not None
    response = client.get(
        f"/api/v1/audit-assignments/{test_audit_assignment.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(test_audit_assignment.id)
    assert content["title"] == test_audit_assignment.title


def test_update_audit_assignment(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_assignment: AuditAssignment,
) -> None:
    assert test_audit_assignment.id is not None
    new_title = random_lower_string()
    data = {"title": new_title, "description": "Updated description"}
    response = client.patch(
        f"/api/v1/audit-assignments/{test_audit_assignment.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == new_title
    assert content["description"] == "Updated description"

    assignment_in_db = db.get(AuditAssignment, test_audit_assignment.id)
    assert assignment_in_db
    assert assignment_in_db.title == new_title


def test_delete_audit_assignment(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_assignment: AuditAssignment,
) -> None:
    assert test_audit_assignment.id is not None
    assignment_id = test_audit_assignment.id
    response = client.delete(
        f"/api/v1/audit-assignments/{assignment_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Audit assignment deleted successfully"

    assignment_in_db = db.get(AuditAssignment, assignment_id)
    assert assignment_in_db is None
