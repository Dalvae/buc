import uuid
from typing import List, Optional

from fastapi import HTTPException
from sqlmodel import Session, select, func

from app.models import AssignedQuestion, AssignedQuestionUpdate, AuditAssignment


def get(*, session: Session, question_id: uuid.UUID, assignment_id: Optional[uuid.UUID] = None) -> Optional[AssignedQuestion]:
    statement = select(AssignedQuestion).where(AssignedQuestion.id == question_id)
    if assignment_id:
        statement = statement.where(AssignedQuestion.audit_assignment_id == assignment_id)
    return session.exec(statement).first()


def get_multi_for_assignment(
    *, session: Session, audit_assignment_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[AssignedQuestion]:
    if not session.get(AuditAssignment, audit_assignment_id):
        raise HTTPException(status_code=404, detail="Audit Assignment not found")
    statement = (
        select(AssignedQuestion)
        .where(AssignedQuestion.audit_assignment_id == audit_assignment_id)
        .order_by(AssignedQuestion.order.asc())
    )
    return list(session.exec(statement).all())


def count_for_assignment(*, session: Session, audit_assignment_id: uuid.UUID) -> int:
    if not session.get(AuditAssignment, audit_assignment_id):
        raise HTTPException(status_code=404, detail="Audit Assignment not found")
    count_statement = (
        select(func.count(AssignedQuestion.id))
        .where(AssignedQuestion.audit_assignment_id == audit_assignment_id)
    )
    count = session.exec(count_statement).one_or_none()
    return count if count is not None else 0


def update(*, session: Session, db_question: AssignedQuestion, question_in: AssignedQuestionUpdate) -> AssignedQuestion:
    if question_in.model_dump(exclude_unset=True).get("question_type"):
        raise HTTPException(status_code=400, detail="Question type of an assigned question cannot be changed")
    
    question_data = question_in.model_dump(exclude_unset=True)
    db_question.sqlmodel_update(question_data)
    session.add(db_question)
    session.flush()
    session.refresh(db_question)
    return db_question


def remove(*, session: Session, question_id: uuid.UUID, assignment_id: uuid.UUID) -> Optional[AssignedQuestion]:
    question = get(session=session, question_id=question_id, assignment_id=assignment_id)
    if not question:
        return None
    session.delete(question)
    session.flush()
    return question

class CRUDAssignedQuestion:
    def get(self, session: Session, *, question_id: uuid.UUID, assignment_id: Optional[uuid.UUID] = None) -> Optional[AssignedQuestion]:
        return get(session=session, question_id=question_id, assignment_id=assignment_id)

    def get_multi_for_assignment(
        self, session: Session, *, audit_assignment_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[AssignedQuestion]:
        return get_multi_for_assignment(
            session=session, audit_assignment_id=audit_assignment_id, skip=skip, limit=limit
        )

    def count_for_assignment(self, session: Session, *, audit_assignment_id: uuid.UUID) -> int:
        return count_for_assignment(session=session, audit_assignment_id=audit_assignment_id)

    def update(
        self, session: Session, *, db_question: AssignedQuestion, question_in: AssignedQuestionUpdate
    ) -> AssignedQuestion:
        return update(session=session, db_question=db_question, question_in=question_in)

    def remove(self, session: Session, *, question_id: uuid.UUID, assignment_id: uuid.UUID) -> Optional[AssignedQuestion]:
        return remove(session=session, question_id=question_id, assignment_id=assignment_id)

assigned_question = CRUDAssignedQuestion()
