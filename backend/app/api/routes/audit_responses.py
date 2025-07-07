import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select

from app.crud.audit_response import audit_response as crud_audit_response
from app.crud.audit_assignment import audit_assignment as crud_audit_assignment
from app.api.deps import (
    CurrentActiveAdminOrSuperuser,
    CurrentActiveAuditor,
    CurrentActiveUser,
    SessionDep,
    obfuscate_data_for_demo_company,
)
from app.models import (
    AuditResponse,
    AuditResponseCreate,
    AuditResponsePublic,
    AuditResponsesPublic,
    AuditResponseUpdate,
    Message,
)

router = APIRouter(prefix="/audit-assignments/{assignment_id}/responses", tags=["audit-responses"])


@router.post(
    "/",
    response_model=AuditResponsePublic,
)
def create_audit_response(
    assignment_id: uuid.UUID,
    *,
    session: SessionDep,
    response_in: AuditResponseCreate,
    current_user: CurrentActiveAuditor,
) -> Any:
    """
    Create a new audit response for a given assignment.
    """
    response = crud_audit_response.create(session=session, response_in=response_in, auditor_id=current_user.id)
    return response


@router.get(
    "/",
    response_model=AuditResponsesPublic,
)
def read_audit_responses_for_assignment(
    assignment_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentActiveUser, # Any user with access to assignment can view responses
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve audit responses for a specific audit assignment.
    """
    # First, check if the user has access to the assignment itself
    assignment = crud_audit_assignment.get(session=session, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Audit Assignment not found")
    if not crud_audit_assignment.can_user_access_assignment(user=current_user, assignment=assignment, session=session):
        raise HTTPException(status_code=403, detail="Not enough permissions to access this audit assignment")

    responses = crud_audit_response.get_multi_for_assignment(session=session, assignment_id=assignment_id, skip=skip, limit=limit)
    count = crud_audit_response.count_for_assignment(session=session, assignment_id=assignment_id)

    responses = obfuscate_data_for_demo_company(responses, current_user)

    return AuditResponsesPublic(data=responses, count=count)


@router.get(
    "/{response_id}",
    response_model=AuditResponsePublic,
)
def read_audit_response_by_id(
    assignment_id: uuid.UUID,
    response_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentActiveUser,
) -> Any:
    """
    Get a specific audit response by id.
    """
    response = crud_audit_response.get(session=session, response_id=response_id, assignment_id=assignment_id)
    if not response:
        raise HTTPException(status_code=404, detail="Audit Response not found or does not belong to this assignment")
    
    # Check if the user has access to the assignment itself
    assignment = crud_audit_assignment.get(session=session, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Audit Assignment not found")
    if not crud_audit_assignment.can_user_access_assignment(user=current_user, assignment=assignment, session=session):
        raise HTTPException(status_code=403, detail="Not enough permissions to access this audit assignment")

    response = obfuscate_data_for_demo_company(response, current_user)
    return response


@router.patch(
    "/{response_id}",
    response_model=AuditResponsePublic,
)
def update_audit_response(
    assignment_id: uuid.UUID,
    response_id: uuid.UUID,
    *,
    session: SessionDep,
    response_in: AuditResponseUpdate,
    current_user: CurrentActiveUser, # Can be auditor (for draft) or admin/superuser (for submitted)
) -> Any:
    """
    Update an audit response.
    """
    response = crud_audit_response.get(session=session, response_id=response_id, assignment_id=assignment_id)
    if not response:
        raise HTTPException(status_code=404, detail="Audit Response not found or does not belong to this assignment")
    
    # Permissions are handled within crud.update_audit_response_db
    updated_response = crud_audit_response.update(session=session, db_response=response, response_in=response_in, current_user=current_user)

    updated_response = obfuscate_data_for_demo_company(updated_response, current_user)
    return updated_response
