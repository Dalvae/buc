import uuid
from typing import List, Optional

from fastapi import HTTPException
from sqlmodel import Session, select, func

from app.audit_types import get_audit_type_definition
from app.models import AuditTemplate, AuditTemplateCreate, AuditTemplateUpdate, QuestionTemplate, User


def get(*, session: Session, template_id: uuid.UUID) -> Optional[AuditTemplate]:
    return session.get(AuditTemplate, template_id)


def get_by_name(*, session: Session, name: str) -> Optional[AuditTemplate]:
    return session.exec(select(AuditTemplate).where(AuditTemplate.name == name)).first()


def get_multi(*, session: Session, skip: int = 0, limit: int = 100) -> List[AuditTemplate]:
    statement = select(AuditTemplate).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def count(*, session: Session) -> int:
    count = session.exec(select(func.count()).select_from(AuditTemplate)).one_or_none()
    return count if count is not None else 0


def create(*, session: Session, template_in: AuditTemplateCreate, creator_id: uuid.UUID) -> AuditTemplate:
    if not get_audit_type_definition(template_in.audit_type_definition_key):
        raise HTTPException(status_code=400, detail="Invalid audit_type_definition_key")
    if get_by_name(session=session, name=template_in.name):
        raise HTTPException(status_code=409, detail="Audit Template name already exists")

    db_template = AuditTemplate.model_validate(template_in, update={"created_by_id": creator_id})
    session.add(db_template)
    session.flush()

    # Create default questions
    audit_type_def = get_audit_type_definition(template_in.audit_type_definition_key)
    if audit_type_def:
        for q_data in audit_type_def.get_default_questions():
            question_create_data = {**q_data, "audit_template_id": db_template.id}
            temp_question_model = QuestionTemplate.model_validate(question_create_data)
            try:
                audit_type_def.validate_question(temp_question_model)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid default question: {e}")
            db_question = QuestionTemplate.model_validate(question_create_data)
            session.add(db_question)
    
    session.flush()
    session.refresh(db_template)
    return db_template


def update(*, session: Session, db_template: AuditTemplate, template_in: AuditTemplateUpdate) -> AuditTemplate:
    template_data = template_in.model_dump(exclude_unset=True)
    if "name" in template_data and template_data["name"] != db_template.name:
        existing = get_by_name(session=session, name=template_data["name"])
        if existing and existing.id != db_template.id:
            raise HTTPException(status_code=409, detail="Audit Template name already exists")

    db_template.sqlmodel_update(template_data)
    session.add(db_template)
    session.flush()
    session.refresh(db_template)
    return db_template


def remove(*, session: Session, template_id: uuid.UUID) -> Optional[AuditTemplate]:
    template = get(session=session, template_id=template_id)
    if not template:
        return None
    if template.audit_assignments:
        raise HTTPException(status_code=400, detail="Cannot delete template with associated assignments")
    
    session.delete(template)
    session.flush()
    return template

class CRUDAuditTemplate:
    def get(self, session: Session, *, template_id: uuid.UUID) -> Optional[AuditTemplate]:
        return get(session=session, template_id=template_id)

    def get_multi(self, session: Session, *, skip: int = 0, limit: int = 100) -> List[AuditTemplate]:
        return get_multi(session=session, skip=skip, limit=limit)

    def count(self, session: Session) -> int:
        return count(session=session)

    def create(self, session: Session, *, template_in: AuditTemplateCreate, creator_id: uuid.UUID) -> AuditTemplate:
        return create(session=session, template_in=template_in, creator_id=creator_id)

    def update(self, session: Session, *, db_template: AuditTemplate, template_in: AuditTemplateUpdate) -> AuditTemplate:
        return update(session=session, db_template=db_template, template_in=template_in)

    def remove(self, session: Session, *, template_id: uuid.UUID) -> Optional[AuditTemplate]:
        return remove(session=session, template_id=template_id)

audit_template = CRUDAuditTemplate()