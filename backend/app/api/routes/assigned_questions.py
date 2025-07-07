import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import func, select

from app.crud.assigned_question import assigned_question as crud_assigned_question
from app.crud.audit_assignment import audit_assignment as crud_audit_assignment
from app.api.deps import SessionDep, get_current_active_user
from app.models import (
    AssignedQuestionPublic,
    AssignedQuestionsPublic,
    AssignedQuestionUpdate,
    Message,
    User,
)

router = APIRouter(prefix="/audit-assignments/{assignment_id}/assigned-questions", tags=["assigned-questions"])


@router.get(
    "/",
    response_model=AssignedQuestionsPublic,
)
def read_assigned_questions_for_assignment(
    assignment_id: uuid.UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user), # Permissions handled by crud.can_user_access_assignment
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve assigned questions for a specific audit assignment.
    """
    assignment = crud_audit_assignment.get(session=session, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Audit Assignment not found")
    
    if not crud_audit_assignment.can_user_access_assignment(user=current_user, assignment=assignment, session=session):
        raise HTTPException(status_code=403, detail="Not enough permissions to access this audit assignment")

    questions = crud_assigned_question.get_multi_for_assignment(session=session, audit_assignment_id=assignment_id, skip=skip, limit=limit)
    count = crud_assigned_question.count_for_assignment(session=session, audit_assignment_id=assignment_id)
    return AssignedQuestionsPublic(data=questions, count=count)


@router.get(
    "/{question_id}",
    response_model=AssignedQuestionPublic,
)
def read_assigned_question_by_id(
    assignment_id: uuid.UUID,
    question_id: uuid.UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user), # Permissions handled by crud.can_user_access_assignment
) -> Any:
    """
    Get a specific assigned question by id for a given audit assignment.
    """
    assignment = crud_audit_assignment.get(session=session, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Audit Assignment not found")
    
    if not crud_audit_assignment.can_user_access_assignment(user=current_user, assignment=assignment, session=session):
        raise HTTPException(status_code=403, detail="Not enough permissions to access this audit assignment")

    question = crud_assigned_question.get(session=session, question_id=question_id, assignment_id=assignment_id)
    if not question:
        raise HTTPException(status_code=404, detail="Assigned Question not found or does not belong to this audit assignment")
    return question


@router.patch(
    "/{question_id}",
    response_model=AssignedQuestionPublic,
)
def update_assigned_question(
    assignment_id: uuid.UUID,
    question_id: uuid.UUID,
    *,
    session: SessionDep,
    question_in: AssignedQuestionUpdate,
    current_user: User = Depends(get_current_active_user),  # noqa: ARG001
) -> Any:
    """
    Update an assigned question for an audit assignment.
    """
    assignment = crud_audit_assignment.get(session=session, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Audit Assignment not found")
    
    # Admin/Superuser check is done by CurrentActiveAdminOrSuperuser dependency

    question = crud_assigned_question.get(session=session, question_id=question_id, assignment_id=assignment_id)
    if not question:
        raise HTTPException(status_code=404, detail="Assigned Question not found or does not belong to this audit assignment")
    
    updated_question = crud_assigned_question.update(session=session, db_question=question, question_in=question_in)
    return updated_question


@router.delete(
    "/{question_id}",
    response_model=Message,
)
def delete_assigned_question(
    assignment_id: uuid.UUID,
    question_id: uuid.UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user),  # noqa: ARG001
) -> Message:
    """
    Delete an assigned question from an audit assignment.
    """
    assignment = crud_audit_assignment.get(session=session, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Audit Assignment not found")
    
    # Admin/Superuser check is done by CurrentActiveAdminOrSuperuser dependency

    question = crud_assigned_question.remove(session=session, question_id=question_id, assignment_id=assignment_id)
    if not question:
        raise HTTPException(status_code=404, detail="Assigned Question not found or does not belong to this audit assignment")
    
    return Message(message="Assigned question deleted successfully")
