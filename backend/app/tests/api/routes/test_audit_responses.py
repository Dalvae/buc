import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.models import (
    AnswerCreate,
    AuditAssignment,
    AuditAssignmentCreate,
    AuditResponse,
    AuditResponseCreate,
    AuditResponseStatus,
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
    QuestionType,
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
    area_in = AreaCreate(name=random_lower_string(), description="Test Area Description")
    assert test_company.id is not None
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


def test_create_audit_response(
    client: TestClient,
    auditor_token_headers: dict[str, str],
    db: Session,
    test_audit_assignment: AuditAssignment,
    test_auditor: User,
) -> None:
    # Assign auditor to the area of the assignment
    if test_audit_assignment.area and test_auditor.id:
        link = UserAreaAssignmentLink(user_id=test_auditor.id, area_id=test_audit_assignment.area.id)
        db.add(link)
        db.commit()
        db.refresh(test_auditor)

    # Get assigned questions for the assignment
    assigned_questions = test_audit_assignment.assigned_questions
    assert len(assigned_questions) > 0

    # Prepare answers for all mandatory questions
    answers_data = []
    for q in assigned_questions:
        if q.question_type == QuestionType.RATING_SCALE:
            answers_data.append({"assigned_question_id": str(q.id), "answer_value": 3})
        elif q.question_type == QuestionType.TEXT:
            answers_data.append({"assigned_question_id": str(q.id), "answer_value": "Some text comment"})
        elif q.question_type == QuestionType.YES_NO:
            answers_data.append({"assigned_question_id": str(q.id), "answer_value": True})

    data = {
        "overall_comments": "Overall comments for the audit",
        "status": "submitted",
        "answers": answers_data,
    }
    response = client.post(
        f"/api/v1/audit-assignments/{test_audit_assignment.id}/responses",
        headers=auditor_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["overall_comments"] == "Overall comments for the audit"
    assert content["status"] == "submitted"
    assert content["auditor_id"] == str(test_auditor.id)
    assert content["audit_assignment_id"] == str(test_audit_assignment.id)
    assert content["score"] is not None
    assert len(content["answers"]) == len(answers_data)

    response_in_db = db.get(AuditResponse, uuid.UUID(content["id"]))
    assert response_in_db is not None
    assert response_in_db.status == AuditResponseStatus.SUBMITTED
    assert response_in_db.score is not None


def test_create_audit_response_draft(
    client: TestClient,
    auditor_token_headers: dict[str, str],
    db: Session,
    test_audit_assignment: AuditAssignment,
    test_auditor: User,
) -> None:
    # Assign auditor to the area of the assignment
    if test_audit_assignment.area and test_auditor.id:
        link = UserAreaAssignmentLink(user_id=test_auditor.id, area_id=test_audit_assignment.area.id)
        db.add(link)
        db.commit()
        db.refresh(test_auditor)

    assigned_questions = test_audit_assignment.assigned_questions
    answers_data = []
    for q in assigned_questions:
        if q.question_type == QuestionType.RATING_SCALE:
            answers_data.append({"assigned_question_id": str(q.id), "answer_value": 2})

    data = {
        "overall_comments": "Draft comments",
        "status": "draft",
        "answers": answers_data,
    }
    response = client.post(
        f"/api/v1/audit-assignments/{test_audit_assignment.id}/responses",
        headers=auditor_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["status"] == "draft"
    assert content["score"] is None  # Score should not be calculated for drafts


def test_read_audit_responses_for_assignment(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_assignment: AuditAssignment,
    test_auditor: User,
) -> None:
    # Create a response first
    if test_audit_assignment.area and test_auditor.id:
        link = UserAreaAssignmentLink(user_id=test_auditor.id, area_id=test_audit_assignment.area.id)
        db.add(link)
        db.commit()
        db.refresh(test_auditor)

    assigned_questions = test_audit_assignment.assigned_questions
    answers_data = []
    for q in assigned_questions:
        if q.question_type == QuestionType.RATING_SCALE:
            answers_data.append({"assigned_question_id": str(q.id), "answer_value": 4})
    response_in = AuditResponseCreate(
        overall_comments="Test response",
        status=AuditResponseStatus.SUBMITTED,
        answers=answers_data,
    )
    assert test_audit_assignment.id is not None # Ensure ID is not None for type checker
    assert test_auditor.id is not None
    crud.audit_response.create(session=db, response_in=response_in, auditor_id=test_auditor.id)

    # Now read responses
    response = client.get(
        f"/api/v1/audit-assignments/{test_audit_assignment.id}/responses",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 1
    assert any(r["audit_assignment_id"] == str(test_audit_assignment.id) for r in content["data"])


def test_read_audit_response_by_id(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_assignment: AuditAssignment,
    test_auditor: User,
) -> None:
    # Create a response first
    if test_audit_assignment.area and test_auditor.id:
        link = UserAreaAssignmentLink(user_id=test_auditor.id, area_id=test_audit_assignment.area.id)
        db.add(link)
        db.commit()
        db.refresh(test_auditor)

    assigned_questions = test_audit_assignment.assigned_questions
    answers_data = []
    for q in assigned_questions:
        if q.question_type == QuestionType.RATING_SCALE:
            answers_data.append({"assigned_question_id": str(q.id), "answer_value": 5})
    response_in = AuditResponseCreate(
        overall_comments="Specific response",
        status=AuditResponseStatus.SUBMITTED,
        answers=answers_data,
    )
    assert test_audit_assignment.id is not None
    assert test_auditor.id is not None
    created_response = crud.audit_response.create(session=db, response_in=response_in, auditor_id=test_auditor.id)

    # Now read the specific response
    response = client.get(
        f"/api/v1/audit-assignments/{test_audit_assignment.id}/responses/{created_response.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(created_response.id)
    assert content["overall_comments"] == "Specific response"


def test_update_audit_response_draft_to_submitted(
    client: TestClient,
    auditor_token_headers: dict[str, str],
    db: Session,
    test_audit_assignment: AuditAssignment,
    test_auditor: User,
) -> None:
    # Assign auditor to the area of the assignment
    if test_audit_assignment.area and test_auditor.id:
        link = UserAreaAssignmentLink(user_id=test_auditor.id, area_id=test_audit_assignment.area.id)
        db.add(link)
        db.commit()
        db.refresh(test_auditor)

    # Create a draft response
    assigned_questions = test_audit_assignment.assigned_questions
    answers_data = []
    for q in assigned_questions:
        if q.question_type == QuestionType.RATING_SCALE:
            answers_data.append({"assigned_question_id": str(q.id), "answer_value": 1})
    draft_response_in = AuditResponseCreate(
        overall_comments="Initial draft",
        status=AuditResponseStatus.DRAFT,
        answers=answers_data,
    )
    draft_response = crud.audit_response.create(session=db, response_in=draft_response_in, auditor_id=test_auditor.id)

    # Update draft to submitted
    update_data = {"overall_comments": "Final comments", "status": "submitted"}
    response = client.patch(
        f"/api/v1/audit-assignments/{test_audit_assignment.id}/responses/{draft_response.id}",
        headers=auditor_token_headers,
        json=update_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["overall_comments"] == "Final comments"
    assert content["status"] == "submitted"
    assert content["score"] is not None  # Score should be calculated now

    response_in_db = db.get(AuditResponse, draft_response.id)
    assert response_in_db is not None
    assert response_in_db.status == AuditResponseStatus.SUBMITTED
    assert response_in_db.score is not None


def test_update_audit_response_submitted_by_auditor_fails(
    client: TestClient,
    auditor_token_headers: dict[str, str],
    db: Session,
    test_audit_assignment: AuditAssignment,
    test_auditor: User,
) -> None:
    # Create a submitted response
    if test_audit_assignment.area and test_auditor.id:
        link = UserAreaAssignmentLink(user_id=test_auditor.id, area_id=test_audit_assignment.area.id)
        db.add(link)
        db.commit()
        db.refresh(test_auditor)

    assigned_questions = test_audit_assignment.assigned_questions
    answers_data = []
    for q in assigned_questions:
        if q.question_type == QuestionType.RATING_SCALE:
            answers_data.append({"assigned_question_id": str(q.id), "answer_value": 3})
    submitted_response_in = AuditResponseCreate(
        overall_comments="Submitted response",
        status=AuditResponseStatus.SUBMITTED,
        answers=answers_data,
    )
    assert test_audit_assignment.id is not None
    assert test_auditor.id is not None
    submitted_response = crud.audit_response.create(session=db, response_in=submitted_response_in, auditor_id=test_auditor.id)

    # Attempt to update submitted response as auditor
    update_data = {"overall_comments": "Attempt to update"}
    response = client.patch(
        f"/api/v1/audit-assignments/{test_audit_assignment.id}/responses/{submitted_response.id}",
        headers=auditor_token_headers,
        json=update_data,
    )
    assert response.status_code == 400
    assert "Cannot update a submitted response" in response.json()["detail"]


def test_update_audit_response_submitted_by_admin_succeeds(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    test_audit_assignment: AuditAssignment,
    test_auditor: User,
) -> None:
    # Create a submitted response
    if test_audit_assignment.area and test_auditor.id:
        link = UserAreaAssignmentLink(user_id=test_auditor.id, area_id=test_audit_assignment.area.id)
        db.add(link)
        db.commit()
        db.refresh(test_auditor)

    assigned_questions = test_audit_assignment.assigned_questions
    answers_data = []
    for q in assigned_questions:
        if q.question_type == QuestionType.RATING_SCALE:
            answers_data.append({"assigned_question_id": str(q.id), "answer_value": 3})
    submitted_response_in = AuditResponseCreate(
        overall_comments="Submitted response",
        status=AuditResponseStatus.SUBMITTED,
        answers=answers_data,
    )
    submitted_response = crud.audit_response.create(session=db, response_in=submitted_response_in, auditor_id=test_auditor.id)

    # Update submitted response as superuser
    update_data = {"overall_comments": "Updated by admin", "score": 95.0}
    response = client.patch(
        f"/api/v1/audit-assignments/{test_audit_assignment.id}/responses/{submitted_response.id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["overall_comments"] == "Updated by admin"
    assert content["score"] == 95.0

    response_in_db = db.get(AuditResponse, submitted_response.id)
    assert response_in_db is not None
    assert response_in_db.overall_comments == "Updated by admin"
    assert response_in_db.score == 95.0
