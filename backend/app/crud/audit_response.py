
import uuid
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlmodel import Session, select, func

from app.audit_types import get_audit_type_definition
from app.crud.audit_assignment import audit_assignment as crud_audit_assignment
from app.crud.assigned_question import assigned_question as crud_assigned_question
from app.crud.answer import answer as crud_answer
from app.models import (
    AuditAssignment,
    AuditResponse,
    AuditResponseCreate,
    AuditResponseUpdate,
    AuditResponseStatus,
    AuditAssignmentStatus,
    AnswerCreate,
    User,
    UserRole,
)


def can_user_respond(user: User, assignment: "AuditAssignment") -> bool:
    if not user or not assignment:
        return False
    if user.role != UserRole.AUDITOR:
        return False
    if user.company_id != assignment.company_id:
        return False
    if assignment.is_public or assignment.area_id is None:
        return True
    if assignment.area_id in {area.id for area in user.assigned_areas}:
        return True
    return False


def get(*, session: Session, response_id: uuid.UUID, assignment_id: Optional[uuid.UUID] = None) -> Optional[AuditResponse]:
    statement = select(AuditResponse).where(AuditResponse.id == response_id)
    if assignment_id:
        statement = statement.where(AuditResponse.audit_assignment_id == assignment_id)
    
    response = session.exec(statement).first()
    if response:
        session.refresh(response, attribute_names=["answers"])
        for ans in response.answers:
            session.refresh(ans, attribute_names=["assigned_question"])
    return response


def get_multi_for_assignment(*, session: Session, assignment_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[AuditResponse]:
    # ... (similar logic as before)
    return []

def count_for_assignment(*, session: Session, assignment_id: uuid.UUID) -> int:
    # ... (similar logic as before)
    return 0


def create(*, session: Session, response_in: AuditResponseCreate, auditor_id: uuid.UUID) -> AuditResponse:
    assignment = crud_audit_assignment.get(session=session, assignment_id=response_in.audit_assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Audit Assignment not found")

    auditor = session.get(User, auditor_id)
    if not auditor or not can_user_respond(user=auditor, assignment=assignment):
        raise HTTPException(status_code=403, detail="User cannot respond to this assignment")

    # ... (rest of the creation logic)
    db_response = AuditResponse.model_validate(
        response_in.model_dump(exclude={"answers"}),
        update={
            "auditor_id": auditor_id,
            "submission_date": datetime.now(timezone.utc) if response_in.status == AuditResponseStatus.SUBMITTED else None
        }
    )
    session.add(db_response)
    session.flush()

    if response_in.answers:
        # ... (answer creation logic)
        pass
    
    session.flush()
    session.refresh(db_response)
    return db_response


def update(*, session: Session, db_response: AuditResponse, response_in: AuditResponseUpdate, current_user: User) -> AuditResponse:
    # ... (update logic with permission checks)
    return db_response

class CRUDAuditResponse:
    def get(self, session: Session, *, response_id: uuid.UUID, assignment_id: Optional[uuid.UUID] = None) -> Optional[AuditResponse]:
        return get(session=session, response_id=response_id, assignment_id=assignment_id)

    def get_multi_for_assignment(self, session: Session, *, assignment_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[AuditResponse]:
        return get_multi_for_assignment(session=session, assignment_id=assignment_id, skip=skip, limit=limit)

    def count_for_assignment(self, session: Session, *, assignment_id: uuid.UUID) -> int:
        return count_for_assignment(session=session, assignment_id=assignment_id)

    def create(self, session: Session, *, response_in: AuditResponseCreate, auditor_id: uuid.UUID) -> AuditResponse:
        return create(session=session, response_in=response_in, auditor_id=auditor_id)

    def update(self, session: Session, *, db_response: AuditResponse, response_in: AuditResponseUpdate, current_user: User) -> AuditResponse:
        return update(session=session, db_response=db_response, response_in=response_in, current_user=current_user)

audit_response = CRUDAuditResponse()
