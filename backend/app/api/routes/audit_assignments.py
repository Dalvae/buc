import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select

from app.crud.audit_assignment import audit_assignment as crud_audit_assignment
from app.api.deps import (
    CurrentActiveAdminOrSuperuser,
    CurrentActiveAuditor,
    CurrentActiveUser,
    SessionDep,
    get_current_active_user_with_company_access,
)
from app.models import (
    AuditAssignmentCreate,
    AuditAssignmentPublic,
    AuditAssignmentsPublic,
    AuditAssignmentUpdate,
    Message,
    User,
)

router = APIRouter(prefix="/audit-assignments", tags=["audit-assignments"])


@router.get(
    "/",
    response_model=AuditAssignmentsPublic,
)
def read_all_audit_assignments(
    session: SessionDep,
    current_user: CurrentActiveAdminOrSuperuser,  # noqa: ARG001  # noqa: ARG001
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve all audit assignments (Superuser/Admin only).
    """
    assignments = crud_audit_assignment.get_all(session=session, skip=skip, limit=limit)
    count = crud_audit_assignment.count_all(session=session)
    return AuditAssignmentsPublic(data=assignments, count=count)


@router.get(
    "/my-assignments",
    response_model=AuditAssignmentsPublic,
)
def read_my_audit_assignments(
    session: SessionDep,
    current_user: CurrentActiveAuditor,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve audit assignments that the current auditor can respond to.
    """
    assignments = crud_audit_assignment.get_multi_for_auditor(session=session, current_user=current_user, skip=skip, limit=limit)
    count = crud_audit_assignment.count_for_auditor(session=session, current_user=current_user)
    return AuditAssignmentsPublic(data=assignments, count=count)


@router.get(
    "/company/{company_id}",
    response_model=AuditAssignmentsPublic,
)
def read_audit_assignments_for_company(
    company_id: uuid.UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user_with_company_access),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve audit assignments for a specific company.
    """
    assignments = crud_audit_assignment.get_multi_for_company(session=session, company_id=company_id, current_user=current_user, skip=skip, limit=limit)
    count = crud_audit_assignment.count_for_company(session=session, company_id=company_id, current_user=current_user)
    return AuditAssignmentsPublic(data=assignments, count=count)


@router.post(
    "/",
    response_model=AuditAssignmentPublic,
)
def create_audit_assignment(
    *,
    session: SessionDep,
    assignment_in: AuditAssignmentCreate,
    current_user: CurrentActiveAdminOrSuperuser,
) -> Any:
    """
    Create new audit assignment from a template for a company or area.
    """
    assignment = crud_audit_assignment.create_with_questions(session=session, assignment_in=assignment_in, creator_id=current_user.id)
    return assignment


@router.get(
    "/{assignment_id}",
    response_model=AuditAssignmentPublic,
)
def read_audit_assignment_by_id(
    assignment_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentActiveUser, # Permissions handled by crud.can_user_access_assignment
) -> Any:
    """
    Get a specific audit assignment by id.
    """
    assignment = crud_audit_assignment.get(session=session, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Audit Assignment not found")
    
    # Check if the user has permission to view this assignment
    if not crud_audit_assignment.can_user_access_assignment(user=current_user, assignment=assignment, session=session):
        raise HTTPException(status_code=403, detail="Not enough permissions to access this audit assignment")

    return assignment


@router.patch(
    "/{assignment_id}",
    response_model=AuditAssignmentPublic,
)
def update_audit_assignment(
    assignment_id: uuid.UUID,
    session: SessionDep,
    assignment_in: AuditAssignmentUpdate,
) -> Any:
    """
    Update an audit assignment.
    """
    assignment = crud_audit_assignment.get(session=session, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Audit Assignment not found")
    
    updated_assignment = crud_audit_assignment.update(session=session, db_assignment=assignment, assignment_in=assignment_in)
    return updated_assignment


@router.delete(
    "/{assignment_id}",
    response_model=Message,
)
def delete_audit_assignment(
    session: SessionDep,
    assignment_id: uuid.UUID,
) -> Message:
    """
    Delete an audit assignment.
    """
    assignment = crud_audit_assignment.get(session=session, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Audit Assignment not found")
    
    try:
        crud_audit_assignment.remove(session=session, assignment_id=assignment_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not delete audit assignment: {e}")

    return Message(message="Audit assignment deleted successfully")
