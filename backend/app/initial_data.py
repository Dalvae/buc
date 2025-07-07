import logging
import uuid

from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.core.db import engine, init_db
from app.models import (
    User, UserCreate, UserRole, Company, CompanyCreate, Area, AreaCreate,
    AuditTemplate, AuditTemplateCreate, AuditAssignment, AuditAssignmentCreate,
    AuditResponseCreate, AuditResponseStatus, QuestionType, UserAreaAssignmentLink
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_superuser(session: Session) -> User:
    user = crud.user.get_by_email(session=session, email=settings.FIRST_SUPERUSER)
    if not user:
        logger.info("Creating superuser")
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
            is_verified=True, # Superuser is always verified
        )
        user = crud.user.create(session=session, user_create=user_in)
    else:
        logger.info("Superuser already exists")
    return user


def create_demo_data(session: Session, superuser: User) -> None:
    logger.info("Creating demo company and data")

    # 1. Create Demo Company
    demo_company_name = "Demo Company"
    demo_company = session.exec(
        select(Company).where(Company.name == demo_company_name)
    ).first()
    if not demo_company:
        company_in = CompanyCreate(name=demo_company_name, details="A company for demonstration purposes", is_demo=True)
        demo_company = crud.company.create(session=session, company_in=company_in)
        logger.info(f"Created demo company: {demo_company.name}")
    else:
        logger.info("Demo company already exists")

    # 2. Create Demo Auditor
    demo_auditor_email = "auditor.demo@example.com"
    demo_auditor = crud.user.get_by_email(session=session, email=demo_auditor_email)
    if not demo_auditor:
        auditor_in = UserCreate(
            email=demo_auditor_email,
            password="changeme",
            full_name="Demo Auditor",
            role=UserRole.AUDITOR,
            company_id=demo_company.id,
            is_verified=True,
        )
        demo_auditor = crud.user.create(session=session, user_create=auditor_in)
        logger.info(f"Created demo auditor: {demo_auditor.email}")
    else:
        logger.info("Demo auditor already exists")

    # 3. Create Areas within Demo Company
    area_names = ["Demo Area 1 (Production)", "Demo Area 2 (Warehouse)", "Demo Area 3 (Office)"]
    demo_areas = []
    for name in area_names:
        area = session.exec(
            select(Area).where(Area.name == name, Area.company_id == demo_company.id)
        ).first()
        if not area:
            area_in = AreaCreate(name=name, description=f"Description for {name}")
            assert demo_company.id is not None
            area = crud.area.create(session=session, area_in=area_in, company_id=demo_company.id)
            logger.info(f"Created demo area: {area.name}")
        else:
            logger.info(f"Demo area {area.name} already exists")
        demo_areas.append(area)

    # 4. Assign Demo Auditor to Demo Areas
    for area in demo_areas:
        link = session.exec(
            select(UserAreaAssignmentLink).where(
                UserAreaAssignmentLink.user_id == demo_auditor.id,
                UserAreaAssignmentLink.area_id == area.id
            )
        ).first()
        if not link:
            link = UserAreaAssignmentLink(user_id=demo_auditor.id, area_id=area.id)
            session.add(link)
            logger.info(f"Assigned demo auditor to area: {area.name}")
    
    session.flush()
    session.refresh(demo_auditor)
    logger.info(f"Demo auditor assigned to areas: {[area.name for area in demo_auditor.assigned_areas]}")

    # 5. Create Audit Templates
    five_s_template_name = "5S Audit Template (Demo)"
    five_s_template = session.exec(
        select(AuditTemplate).where(AuditTemplate.name == five_s_template_name)
    ).first()
    if not five_s_template:
        five_s_template_in = AuditTemplateCreate(
            name=five_s_template_name,
            description="Standard 5S audit for demo purposes",
            audit_type_definition_key="FIVE_S_AUDIT",
        )
        five_s_template = crud.audit_template.create(session=session, template_in=five_s_template_in, creator_id=superuser.id)
        logger.info(f"Created 5S Audit Template: {five_s_template.name}")
    else:
        logger.info("5S Audit Template already exists")

    security_template_name = "Security Checklist (Demo)"
    security_template = session.exec(
        select(AuditTemplate).where(AuditTemplate.name == security_template_name)
    ).first()
    if not security_template:
        security_template_in = AuditTemplateCreate(
            name=security_template_name,
            description="Basic security checklist for demo purposes",
            audit_type_definition_key="SECURITY_CHECKLIST_AUDIT",
        )
        security_template = crud.audit_template.create(session=session, template_in=security_template_in, creator_id=superuser.id)
        logger.info(f"Created Security Checklist Template: {security_template.name}")
    else:
        logger.info("Security Checklist Template already exists")

    # 6. Create Audit Assignments
    if five_s_template and demo_areas:
        assignment_name = f"5S Audit - {demo_areas[0].name}"
        assignment = session.exec(
            select(AuditAssignment).where(AuditAssignment.title == assignment_name)
        ).first()
        if not assignment:
            assignment_in = AuditAssignmentCreate(
                audit_template_id=five_s_template.id,
                company_id=demo_company.id,
                area_id=demo_areas[0].id,
                title=assignment_name,
                description="Monthly 5S audit for Demo Area 1",
                is_public=True, # Make it public for demo
            )
            crud.audit_assignment.create_with_questions(session=session, assignment_in=assignment_in, creator_id=superuser.id)
            logger.info(f"Created audit assignment: {assignment_name}")
        else:
            logger.info(f"Audit assignment {assignment_name} already exists")

    if security_template and demo_areas:
        assignment_name = f"Security Audit - {demo_areas[1].name}"
        assignment = session.exec(
            select(AuditAssignment).where(AuditAssignment.title == assignment_name)
        ).first()
        if not assignment:
            assignment_in = AuditAssignmentCreate(
                audit_template_id=security_template.id,
                company_id=demo_company.id,
                area_id=demo_areas[1].id,
                title=assignment_name,
                description="Weekly security audit for Demo Area 2",
                is_public=True, # Make it public for demo
            )
            crud.audit_assignment.create_with_questions(session=session, assignment_in=assignment_in, creator_id=superuser.id)
            logger.info(f"Created audit assignment: {assignment_name}")
        else:
            logger.info(f"Audit assignment {assignment_name} already exists")

    # 7. Optionally, create some Audit Responses
    # This part can be expanded to create realistic responses
    logger.info("Demo data creation complete.")


def init() -> None:
    with Session(engine) as session:
        init_db(session)
        superuser = create_superuser(session)
        create_demo_data(session, superuser)
        session.commit()


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
