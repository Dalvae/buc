import uuid
from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select

from app.crud.audit_template import audit_template as crud_audit_template
from app.crud.question_template import question_template as crud_question_template
from app.api.deps import (
    CurrentActiveAdminOrSuperuser,
    CurrentActiveUser,
    SessionDep,
)
from app.models import (
    AuditTemplate,
    AuditTemplateCreate,
    AuditTemplatePublic,
    AuditTemplatesPublic,
    AuditTemplateUpdate,
    QuestionTemplate,
    QuestionTemplateCreate,
    QuestionTemplatePublic,
    QuestionTemplatesPublic,
    QuestionTemplateUpdate,
    Message,
)
from app.audit_types import get_audit_type_definition, AUDIT_TYPE_DEFINITIONS

router = APIRouter(prefix="/audit-templates", tags=["audit-templates"])


@router.get(
    "/",
    response_model=AuditTemplatesPublic,
)
def read_audit_templates(
    session: SessionDep,
    current_user: CurrentActiveUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve audit templates.
    """
    templates = crud_audit_template.get_multi(session=session, skip=skip, limit=limit)
    count = crud_audit_template.count(session=session)
    return AuditTemplatesPublic(data=templates, count=count)


@router.get(
    "/types",
    response_model=List[Dict[str, str]], # Return a list of dicts with key and name
)
def get_audit_template_types() -> Any:
    """
    Get a list of available code-defined audit template types.
    """
    return [{
        "key": key,
        "name": AUDIT_TYPE_DEFINITIONS[key]().get_name()
    } for key in AUDIT_TYPE_DEFINITIONS.keys()]


@router.post(
    "/",
    response_model=AuditTemplatePublic,
)
def create_audit_template(
    *,
    session: SessionDep,
    template_in: AuditTemplateCreate,
    current_user: CurrentActiveAdminOrSuperuser,
) -> Any:
    """
    Create new audit template.
    """
    template = crud_audit_template.create(session=session, template_in=template_in, creator_id=current_user.id)
    return template


@router.get(
    "/{template_id}",
    response_model=AuditTemplatePublic,
)
def read_audit_template(
    template_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """
    Get a specific audit template by id.
    """
    template = crud_audit_template.get(session=session, template_id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Audit Template not found")
    return template


@router.patch(
    "/{template_id}",
    response_model=AuditTemplatePublic,
)
def update_audit_template(
    template_id: uuid.UUID,
    session: SessionDep,
    template_in: AuditTemplateUpdate,
) -> Any:
    """
    Update an audit template.
    """
    template = crud_audit_template.get(session=session, template_id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Audit Template not found")
    
    template = crud_audit_template.update(session=session, db_template=template, template_in=template_in)
    return template





# Question Template Endpoints (nested under audit-templates)

@router.get(
    "/{template_id}/questions",
    response_model=QuestionTemplatesPublic,
)
def read_question_templates_for_audit_template(
    template_id: uuid.UUID,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve question templates for a specific audit template.
    """
    questions = crud_question_template.get_multi_for_template(session=session, audit_template_id=template_id, skip=skip, limit=limit)
    count = crud_question_template.count_for_template(session=session, audit_template_id=template_id)
    return QuestionTemplatesPublic(data=questions, count=count)


@router.post(
    "/{template_id}/questions",
    response_model=QuestionTemplatePublic,
)
def create_question_template(
    template_id: uuid.UUID,
    session: SessionDep,
    question_in: QuestionTemplateCreate,
) -> Any:
    """
    Create new question template for an audit template.
    """
    if question_in.audit_template_id != template_id:
        raise HTTPException(status_code=400, detail="Audit template ID in path and body do not match.")
    
    question = crud_question_template.create(session=session, question_in=question_in)
    return question


@router.get(
    "/{template_id}/questions/{question_id}",
    response_model=QuestionTemplatePublic,
)
def read_question_template_by_id(
    template_id: uuid.UUID,
    question_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """
    Get a specific question template by id for a given audit template.
    """
    question = crud_question_template.get(session=session, question_id=question_id, audit_template_id=template_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question Template not found or does not belong to this audit template")
    return question


@router.patch(
    "/{template_id}/questions/{question_id}",
    response_model=QuestionTemplatePublic,
)
def update_question_template(
    template_id: uuid.UUID,
    question_id: uuid.UUID,
    *,
    session: SessionDep,
    question_in: QuestionTemplateUpdate,
) -> Any:
    """
    Update a question template for an audit template.
    """
    question = crud_question_template.get(session=session, question_id=question_id, audit_template_id=template_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question Template not found or does not belong to this audit template")
    
    updated_question = crud_question_template.update(session=session, db_question=question, question_in=question_in)
    return updated_question


@router.delete(
    "/{template_id}/questions/{question_id}",
    response_model=Message,
)
def delete_question_template(
    template_id: uuid.UUID,
    question_id: uuid.UUID,
    session: SessionDep,
) -> Message:
    """
    Delete a question template from an audit template.
    """
    question = crud_question_template.remove(session=session, question_id=question_id, audit_template_id=template_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question Template not found or does not belong to this audit template")
    
    return Message(message="Question template deleted successfully")
