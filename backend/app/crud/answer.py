
import uuid
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session

from app.models import Answer, AnswerCreate, AssignedQuestion


def _validate_answer_value(answer_value: Any, assigned_question: AssignedQuestion, audit_type_def: Any) -> None:
    if assigned_question.question_type == "YES_NO":
        if not isinstance(answer_value, bool) and answer_value not in ["yes", "no", "true", "false", None]:
            raise HTTPException(status_code=400, detail="Invalid answer value for YES_NO question")
    # Add more validation as needed


def create(*, session: Session, answer_in: AnswerCreate, audit_response_id: uuid.UUID, audit_type_def: Any) -> Answer:
    assigned_question = session.get(AssignedQuestion, answer_in.assigned_question_id)
    if not assigned_question:
        raise HTTPException(status_code=404, detail="Assigned Question not found")

    _validate_answer_value(answer_in.answer_value, assigned_question, audit_type_def)

    db_answer = Answer.model_validate(answer_in, update={"audit_response_id": audit_response_id})
    session.add(db_answer)
    session.flush()
    session.refresh(db_answer)
    return db_answer

class CRUDAnswer:
    def create(self, session: Session, *, answer_in: AnswerCreate, audit_response_id: uuid.UUID, audit_type_def: Any) -> Answer:
        return create(session=session, answer_in=answer_in, audit_response_id=audit_response_id, audit_type_def=audit_type_def)

answer = CRUDAnswer()
