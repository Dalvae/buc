import uuid
from typing import List, Optional, Any

from fastapi import HTTPException
from sqlmodel import Session, select, func, or_

from app.crud.audit_template import audit_template
from app.crud.company import company
from app.crud.area import area
from app.models import (
    AuditAssignment,
    AuditAssignmentCreate,
    AuditAssignmentUpdate,
    AuditAssignmentStatus,
    AssignedQuestion,
    AssignedQuestionCreate,
    User,
    UserRole,
)


def get(*, session: Session, assignment_id: uuid.UUID) -> Optional[AuditAssignment]:
    return session.get(AuditAssignment, assignment_id)


def get_all(*, session: Session, skip: int = 0, limit: int = 100) -> List[AuditAssignment]:
    statement = select(AuditAssignment).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def count_all(*, session: Session) -> int:
    count = session.exec(select(func.count(AuditAssignment.id))).one_or_none()
    return count if count is not None else 0


def _get_auditor_assignment_conditions(current_user: User) -> list[Any]:
    user_assigned_area_ids = {area.id for area in current_user.assigned_areas if area.id}
    return [
        AuditAssignment.company_id == current_user.company_id,
        or_(
            AuditAssignment.is_public,
            AuditAssignment.area_id.is_(None),
            AuditAssignment.area_id.in_(user_assigned_area_ids),
        ),
    ]


def get_multi_for_auditor(*, session: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[AuditAssignment]:
    if current_user.role != UserRole.AUDITOR and not current_user.is_superuser:
        return []
    if not current_user.company_id:
        return []

    conditions = _get_auditor_assignment_conditions(current_user)
    statement = (
        select(AuditAssignment)
        .where(*conditions)
        .order_by(AuditAssignment.due_date.desc().nulls_last(), AuditAssignment.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def count_for_auditor(*, session: Session, current_user: User) -> int:
    if current_user.role != UserRole.AUDITOR and not current_user.is_superuser:
        return 0
    if not current_user.company_id:
        return 0

    conditions = _get_auditor_assignment_conditions(current_user)
    count_statement = select(func.count(AuditAssignment.id)).where(*conditions)
    count = session.exec(count_statement).one_or_none()
    return count if count is not None else 0


def get_multi_for_company(
    *, session: Session, company_id: uuid.UUID, current_user: User, skip: int = 0, limit: int = 100
) -> List[AuditAssignment]:
    # Permission checks
    base_query = select(AuditAssignment).where(AuditAssignment.company_id == company_id)
    # ... additional permission logic ...
    statement = base_query.offset(skip).limit(limit)
    return list(session.exec(statement).all())


def count_for_company(*, session: Session, company_id: uuid.UUID, current_user: User) -> int:
    # Permission checks
    base_query = select(func.count(AuditAssignment.id)).where(AuditAssignment.company_id == company_id)
    # ... additional permission logic ...
    count = session.exec(base_query).one_or_none()
    return count if count is not None else 0


def create_with_questions(*, session: Session, assignment_in: AuditAssignmentCreate, creator_id: uuid.UUID) -> AuditAssignment:
    template = audit_template.get(session=session, template_id=assignment_in.audit_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Audit Template not found")
    if not company.get(session=session, company_id=assignment_in.company_id):
        raise HTTPException(status_code=404, detail="Company not found")
    if assignment_in.area_id and not area.get(session=session, area_id=assignment_in.area_id, company_id=assignment_in.company_id):
        raise HTTPException(status_code=404, detail="Area not found or does not belong to the company")

    db_assignment = AuditAssignment.model_validate(
        assignment_in,
        update={"created_by_id": creator_id, "status": AuditAssignmentStatus.PENDING},
    )
    session.add(db_assignment)
    session.flush()

    for qt in template.question_templates:
        assigned_q_create = AssignedQuestionCreate(
            text=qt.text,
            question_type=qt.question_type,
            options=qt.options,
            order=qt.order,
            is_mandatory=qt.is_mandatory,
            section_id=qt.section_id,
            audit_assignment_id=db_assignment.id,
            original_question_template_id=qt.id,
        )
        db_assigned_question = AssignedQuestion.model_validate(assigned_q_create)
        session.add(db_assigned_question)

    session.flush()
    session.refresh(db_assignment)
    return db_assignment


def update(*, session: Session, db_assignment: AuditAssignment, assignment_in: AuditAssignmentUpdate) -> AuditAssignment:
    assignment_data = assignment_in.model_dump(exclude_unset=True)
    if "area_id" in assignment_data and assignment_data["area_id"] != db_assignment.area_id:
        if assignment_data["area_id"] is not None:
            if not area.get(session=session, area_id=assignment_data["area_id"], company_id=db_assignment.company_id):
                raise HTTPException(status_code=404, detail="New area not found")

    db_assignment.sqlmodel_update(assignment_data)
    session.add(db_assignment)
    session.flush()
    session.refresh(db_assignment)
    return db_assignment


def remove(*, session: Session, assignment_id: uuid.UUID) -> Optional[AuditAssignment]:
    assignment = get(session=session, assignment_id=assignment_id)
    if not assignment:
        return None
    session.delete(assignment)
    session.flush()
    return assignment

def can_user_access_assignment(user: User, assignment: AuditAssignment, session: Session) -> bool:
    if not user or not assignment:
        return False

    if user.is_superuser or user.role == UserRole.ADMIN:
        return True

    if user.company_id != assignment.company_id:
        return False

    if assignment.is_public:
        return True

    if assignment.area_id is None:
        return True

    if assignment.area_id is not None:
        if assignment.area_id in [area.id for area in user.assigned_areas]:
            return True

    return False


class CRUDAuditAssignment:
    def get(self, session: Session, *, assignment_id: uuid.UUID) -> Optional[AuditAssignment]:
        return get(session=session, assignment_id=assignment_id)

    def get_all(self, session: Session, *, skip: int = 0, limit: int = 100) -> List[AuditAssignment]:
        return get_all(session=session, skip=skip, limit=limit)

    def count_all(self, session: Session) -> int:
        return count_all(session=session)
    
    def get_multi_for_auditor(self, session: Session, *, current_user: User, skip: int = 0, limit: int = 100) -> List[AuditAssignment]:
        return get_multi_for_auditor(session=session, current_user=current_user, skip=skip, limit=limit)

    def count_for_auditor(self, session: Session, *, current_user: User) -> int:
        return count_for_auditor(session=session, current_user=current_user)

    def get_multi_for_company(
        self, session: Session, *, company_id: uuid.UUID, current_user: User, skip: int = 0, limit: int = 100
    ) -> List[AuditAssignment]:
        return get_multi_for_company(
            session=session, company_id=company_id, current_user=current_user, skip=skip, limit=limit
        )

    def count_for_company(self, session: Session, *, company_id: uuid.UUID, current_user: User) -> int:
        return count_for_company(session=session, company_id=company_id, current_user=current_user)

    def create_with_questions(
        self, session: Session, *, assignment_in: AuditAssignmentCreate, creator_id: uuid.UUID
    ) -> AuditAssignment:
        return create_with_questions(session=session, assignment_in=assignment_in, creator_id=creator_id)

    def update(
        self, session: Session, *, db_assignment: AuditAssignment, assignment_in: AuditAssignmentUpdate
    ) -> AuditAssignment:
        return update(session=session, db_assignment=db_assignment, assignment_in=assignment_in)

    def remove(self, session: Session, *, assignment_id: uuid.UUID) -> Optional[AuditAssignment]:
        return remove(session=session, assignment_id=assignment_id)
    
    def can_user_access_assignment(self, user: User, assignment: AuditAssignment, session: Session) -> bool:
        return can_user_access_assignment(user=user, assignment=assignment, session=session)

audit_assignment = CRUDAuditAssignment()