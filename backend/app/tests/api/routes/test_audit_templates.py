import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.models import AuditTemplate, AuditTemplateCreate, User, UserCreate, UserRole, QuestionTemplate
from app.tests.utils.utils import random_email, random_lower_string


@pytest.fixture(name="test_superuser")
def test_superuser_fixture(db: Session) -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = crud.user.create(session=db, user_create=user_in)
    return user


@pytest.fixture(name="test_audit_template")
def test_audit_template_fixture(db: Session, test_superuser: User) -> AuditTemplate:
    template_in = AuditTemplateCreate(
        name=random_lower_string(),
        description="Test Audit Template",
        audit_type_definition_key="FIVE_S_AUDIT",
    )
    template = crud.audit_template.create(session=db, template_in=template_in, creator_id=test_superuser.id)
    return template


def test_create_audit_template(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_superuser: User,
) -> None:
    name = random_lower_string()
    data = {
        "name": name,
        "description": "A new audit template",
        "audit_type_definition_key": "FIVE_S_AUDIT",
    }
    response = client.post(
        f"/api/v1/audit-templates/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == name
    assert content["description"] == "A new audit template"
    assert content["audit_type_definition_key"] == "FIVE_S_AUDIT"
    assert "id" in content
    assert "created_by_id" in content

    template_in_db = db.get(AuditTemplate, uuid.UUID(content["id"]))
    assert template_in_db
    assert template_in_db.name == name
    assert len(template_in_db.question_templates) > 0 # Should create default questions


def test_create_audit_template_invalid_type(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    name = random_lower_string()
    data = {
        "name": name,
        "description": "A new audit template",
        "audit_type_definition_key": "NON_EXISTENT_AUDIT_TYPE",
    }
    response = client.post(
        f"/api/v1/audit-templates/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 400
    assert "Invalid audit_type_definition_key" in response.json()["detail"]


def test_read_audit_templates(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_template: AuditTemplate,
) -> None:
    response = client.get(
        f"/api/v1/audit-templates/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 1
    assert any(t["id"] == str(test_audit_template.id) for t in content["data"])


def test_read_audit_template_by_id(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_template: AuditTemplate,
) -> None:
    response = client.get(
        f"/api/v1/audit-templates/{test_audit_template.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(test_audit_template.id)
    assert content["name"] == test_audit_template.name


def test_update_audit_template(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_template: AuditTemplate,
) -> None:
    new_name = random_lower_string()
    data = {"name": new_name, "description": "Updated description"}
    response = client.patch(
        f"/api/v1/audit-templates/{test_audit_template.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == new_name
    assert content["description"] == "Updated description"

    template_in_db = db.get(AuditTemplate, test_audit_template.id)
    assert template_in_db
    assert template_in_db.name == new_name


def test_delete_audit_template(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_template: AuditTemplate,
) -> None:
    template_id = test_audit_template.id
    response = client.delete(
        f"/api/v1/audit-templates/{template_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Audit template deleted successfully"

    template_in_db = db.get(AuditTemplate, template_id)
    assert template_in_db is None


def test_read_question_templates_for_audit_template(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_template: AuditTemplate,
) -> None:
    response = client.get(
        f"/api/v1/audit-templates/{test_audit_template.id}/questions",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) > 0
    assert "id" in content["data"][0]
    assert "text" in content["data"][0]


def test_create_question_template(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_template: AuditTemplate,
) -> None:
    data = {
        "audit_template_id": str(test_audit_template.id),
        "text": "New question?",
        "question_type": "yes_no",
        "options": {},
        "order": 10,
        "is_mandatory": True,
    }
    response = client.post(
        f"/api/v1/audit-templates/{test_audit_template.id}/questions",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["text"] == "New question?"
    assert content["question_type"] == "yes_no"

    question_in_db = db.get(QuestionTemplate, uuid.UUID(content["id"]))
    assert question_in_db
    assert question_in_db.text == "New question?"


def test_create_question_template_invalid_type(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_template: AuditTemplate,
) -> None:
    # Attempt to create a question type not allowed by FIVE_S_AUDIT (e.g., YES_NO with options)
    data = {
        "audit_template_id": str(test_audit_template.id),
        "text": "Invalid question?",
        "question_type": "yes_no", # Not allowed for 5S
        "options": {},
        "order": 10,
        "is_mandatory": True,
    }
    response = client.post(
        f"/api/v1/audit-templates/{test_audit_template.id}/questions",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 400
    assert "not allowed for 5S Audit" in response.json()["detail"]


def test_read_question_template_by_id(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_template: AuditTemplate,
) -> None:
    # Get an existing question from the template
    question = test_audit_template.question_templates[0]
    response = client.get(
        f"/api/v1/audit-templates/{test_audit_template.id}/questions/{question.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(question.id)
    assert content["text"] == question.text


def test_update_question_template(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_template: AuditTemplate,
) -> None:
    question = test_audit_template.question_templates[0]
    new_text = "Updated question text?"
    data = {"text": new_text, "order": 99}
    response = client.patch(
        f"/api/v1/audit-templates/{test_audit_template.id}/questions/{question.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["text"] == new_text
    assert content["order"] == 99

    question_in_db = db.get(QuestionTemplate, question.id)
    assert question_in_db
    assert question_in_db.text == new_text
    assert question_in_db.order == 99


def test_delete_question_template(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_template: AuditTemplate,
) -> None:
    question = test_audit_template.question_templates[0]
    question_id = question.id
    response = client.delete(
        f"/api/v1/audit-templates/{test_audit_template.id}/questions/{question_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Question template deleted successfully"

    question_in_db = db.get(QuestionTemplate, question_id)
    assert question_in_db is None
