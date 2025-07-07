import uuid
from typing import List, Optional

from fastapi import HTTPException
from sqlmodel import Session, select, func

from app.audit_types import get_audit_type_definition
from app.models import QuestionTemplate, QuestionTemplateCreate, QuestionTemplateUpdate, AuditTemplate


def get(*, session: Session, question_id: uuid.UUID, audit_template_id: Optional[uuid.UUID] = None) -> Optional[QuestionTemplate]:
    statement = select(QuestionTemplate).where(QuestionTemplate.id == question_id)
    if audit_template_id:
        statement = statement.where(QuestionTemplate.audit_template_id == audit_template_id)
    return session.exec(statement).first()


def get_multi_for_template(
    *, session: Session, audit_template_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[QuestionTemplate]:
    if not session.get(AuditTemplate, audit_template_id):
        raise HTTPException(status_code=404, detail="Audit Template not found")
    statement = (
        select(QuestionTemplate)
        .where(QuestionTemplate.audit_template_id == audit_template_id)
        .order_by(QuestionTemplate.order)
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def count_for_template(*, session: Session, audit_template_id: uuid.UUID) -> int:
    if not session.get(AuditTemplate, audit_template_id):
        raise HTTPException(status_code=404, detail="Audit Template not found")
    count_statement = (
        select(func.count(QuestionTemplate.id))
        .where(QuestionTemplate.audit_template_id == audit_template_id)
    )
    count = session.exec(count_statement).one_or_none()
    return count if count is not None else 0


def create(*, session: Session, question_in: QuestionTemplateCreate) -> QuestionTemplate:
    audit_template = session.get(AuditTemplate, question_in.audit_template_id)
    if not audit_template:
        raise HTTPException(status_code=404, detail="Audit Template not found")

    audit_type_def = get_audit_type_definition(audit_template.audit_type_definition_key)
    if not audit_type_def:
        raise HTTPException(status_code=500, detail="Audit Type Definition not found")

    temp_question_model = QuestionTemplate.model_validate(question_in)
    try:
        audit_type_def.validate_question(temp_question_model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db_question = QuestionTemplate.model_validate(question_in)
    session.add(db_question)
    session.flush()
    session.refresh(db_question)
    return db_question


def update(*, session: Session, db_question: QuestionTemplate, question_in: QuestionTemplateUpdate) -> QuestionTemplate:
    audit_template = session.get(AuditTemplate, db_question.audit_template_id)
    if not audit_template:
        raise HTTPException(status_code=404, detail="Associated Audit Template not found")

    audit_type_def = get_audit_type_definition(audit_template.audit_type_definition_key)
    if not audit_type_def:
        raise HTTPException(status_code=500, detail="Audit Type Definition not found")

    question_data = question_in.model_dump(exclude_unset=True)
    updated_question_for_validation = db_question.model_copy(update=question_data)
    try:
        audit_type_def.validate_question(updated_question_for_validation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db_question.sqlmodel_update(question_data)
    session.add(db_question)
    session.flush()
    session.refresh(db_question)
    return db_question


def remove(*, session: Session, question_id: uuid.UUID, audit_template_id: uuid.UUID) -> Optional[QuestionTemplate]:
    question = get(session=session, question_id=question_id, audit_template_id=audit_template_id)
    if not question:
        return None
    session.delete(question)
    session.flush()
    return question

class CRUDQuestionTemplate:
    def get(self, session: Session, *, question_id: uuid.UUID, audit_template_id: Optional[uuid.UUID] = None) -> Optional[QuestionTemplate]:
        return get(session=session, question_id=question_id, audit_template_id=audit_template_id)

    def get_multi_for_template(
        self, session: Session, *, audit_template_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[QuestionTemplate]:
        return get_multi_for_template(
            session=session, audit_template_id=audit_template_id, skip=skip, limit=limit
        )

    def count_for_template(self, session: Session, *, audit_template_id: uuid.UUID) -> int:
        return count_for_template(session=session, audit_template_id=audit_template_id)

    def create(self, session: Session, *, question_in: QuestionTemplateCreate) -> QuestionTemplate:
        return create(session=session, question_in=question_in)

    def update(
        self, session: Session, *, db_question: QuestionTemplate, question_in: QuestionTemplateUpdate
    ) -> QuestionTemplate:
        return update(session=session, db_question=db_question, question_in=question_in)

    def remove(self, session: Session, *, question_id: uuid.UUID, audit_template_id: uuid.UUID) -> Optional[QuestionTemplate]:
        return remove(session=session, question_id=question_id, audit_template_id=audit_template_id)

question_template = CRUDQuestionTemplate()