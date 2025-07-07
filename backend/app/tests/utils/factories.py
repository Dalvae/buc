import random
from typing import Optional
import uuid

from sqlmodel import Session

from app import crud
from app.models import (
    User, UserCreate, UserRole,
    Company, CompanyCreate,
    Area, AreaCreate,
    AuditTemplate, AuditTemplateCreate,
    QuestionTemplate, QuestionTemplateCreate, QuestionType,
    AuditAssignment, AuditAssignmentCreate,
    AuditResponse, AuditResponseCreate, AnswerCreate, AuditResponseStatus
)
from app.tests.utils.utils import random_email, random_lower_string

def create_random_user(
    db: Session,
    *,
    role: UserRole = UserRole.USER,
    is_superuser: bool = False,
    company_id: Optional[uuid.UUID] = None,
    is_verified: bool = True
) -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(
        email=email,
        password=password,
        role=role,
        is_superuser=is_superuser,
        company_id=company_id,
        is_verified=is_verified,
        full_name=random_lower_string().title()
    )
    return crud.user.create(session=db, user_create=user_in)

def create_random_company(db: Session, *, is_demo: bool = False) -> Company:
    name = f"Company {random_lower_string(6)}"
    company_in = CompanyCreate(name=name, is_demo=is_demo)
    return crud.company.create(session=db, company_in=company_in)

def create_random_area(db: Session, *, company_id: uuid.UUID) -> Area:
    name = f"Area {random_lower_string(6)}"
    area_in = AreaCreate(name=name)
    return crud.area.create(session=db, area_in=area_in, company_id=company_id)

def create_random_audit_template(db: Session, *, creator_id: uuid.UUID) -> AuditTemplate:
    name = f"Template {random_lower_string()}"
    template_in = AuditTemplateCreate(
        name=name,
        description="A test audit template",
        audit_type_definition_key="FIVE_S_AUDIT"
    )
    return crud.audit_template.create(session=db, template_in=template_in, creator_id=creator_id)

def create_random_audit_assignment(
    db: Session, *, audit_template_id: uuid.UUID, company_id: uuid.UUID, creator_id: uuid.UUID, area_id: Optional[uuid.UUID] = None
) -> AuditAssignment:
    assignment_in = AuditAssignmentCreate(
        title=f"Assignment {random_lower_string()}",
        audit_template_id=audit_template_id,
        company_id=company_id,
        area_id=area_id
    )
    return crud.audit_assignment.create_with_questions(session=db, assignment_in=assignment_in, creator_id=creator_id)

def create_random_audit_response(
    db: Session, *, assignment_id: uuid.UUID, auditor_id: uuid.UUID, status: AuditResponseStatus = AuditResponseStatus.SUBMITTED
) -> AuditResponse:
    assignment = crud.audit_assignment.get(session=db, assignment_id=assignment_id)
    assert assignment is not None
    answers = []
    for q in assignment.assigned_questions:
        if q.question_type == QuestionType.RATING_SCALE:
            answers.append(AnswerCreate(assigned_question_id=q.id, answer_value=random.randint(1, 5)))
        elif q.question_type == QuestionType.TEXT:
             answers.append(AnswerCreate(assigned_question_id=q.id, answer_value="Random comment"))
    
    response_in = AuditResponseCreate(
        audit_assignment_id=assignment_id,
        status=status,
        answers=answers
    )
    return crud.audit_response.create(session=db, response_in=response_in, auditor_id=auditor_id)
