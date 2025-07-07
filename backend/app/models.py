import enum
import uuid
from datetime import datetime, date
from typing import List, Optional, Any

import sqlalchemy as sa
from pydantic import model_validator
from sqlalchemy.dialects import postgresql
from sqlmodel import Field, Relationship, SQLModel


# Enums defined in one place for consistency
class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"
    USER = "USER"


class QuestionType(str, enum.Enum):
    TEXT = "TEXT"
    MULTIPLE_CHOICE_SINGLE = "MULTIPLE_CHOICE_SINGLE"
    MULTIPLE_CHOICE_MULTIPLE = "MULTIPLE_CHOICE_MULTIPLE"
    YES_NO = "YES_NO"
    RATING_SCALE = "RATING_SCALE"
    SECTION_HEADER = "SECTION_HEADER"


class AuditAssignmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"


class AuditPeriodicity(str, enum.Enum):
    ONE_TIME = "ONE_TIME"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUALLY = "ANNUALLY"


class AuditResponseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"


# Generic and auth-related API Schemas
# Placed at top to avoid circular import issues
class Message(SQLModel):
    message: str

class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(SQLModel):
    sub: Optional[uuid.UUID] = None

class NewPassword(SQLModel):
    token: str
    new_password: str

class UpdatePassword(SQLModel):
    current_password: str
    new_password: str

class UserUpdateMe(SQLModel):
    full_name: Optional[str] = None
    email: Optional[str] = None

class UserRegister(SQLModel):
    email: str
    password: str
    full_name: Optional[str] = None
    company_id: uuid.UUID

class PrivateUserCreate(SQLModel):
    email: str
    password: str
    full_name: str
    is_verified: bool = False


# Link table model for Many-to-Many relationship between User and Area
class UserAreaAssignmentLink(SQLModel, table=True):
    __tablename__ = "user_area_assignment_link"
    user_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    area_id: uuid.UUID = Field(foreign_key="area.id", primary_key=True)
    assigned_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now()},
    )

    user: "User" = Relationship(back_populates="area_links")
    area: "Area" = Relationship(back_populates="user_links")


# Base model for shared User fields
class UserBase(SQLModel):
    email: str = Field(unique=True, index=True, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    full_name: Optional[str] = Field(default=None, max_length=255)
    role: UserRole = Field(default=UserRole.USER, sa_column=sa.Column(sa.Enum(UserRole)))
    is_verified: bool = Field(default=False)
    company_id: Optional[uuid.UUID] = Field(default=None, foreign_key="company.id")


# Database model for User
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str = Field()
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now()},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now(), "onupdate": sa.func.now()},
    )

    company: Optional["Company"] = Relationship(
        back_populates="users", sa_relationship_kwargs={"foreign_keys": "[User.company_id]"}
    )
    area_links: List["UserAreaAssignmentLink"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    @property
    def assigned_areas(self) -> List["Area"]:
        return [link.area for link in self.area_links]

    audit_assignments_created: List["AuditAssignment"] = Relationship(back_populates="created_by")
    audit_responses: List["AuditResponse"] = Relationship(back_populates="auditor")
    audit_templates_created: List["AuditTemplate"] = Relationship(back_populates="created_by")


# Base model for shared Company fields
class CompanyBase(SQLModel):
    name: str = Field(unique=True, index=True, max_length=255)
    details: Optional[str] = Field(default=None)
    is_demo: bool = Field(default=False)


# Database model for Company
class Company(CompanyBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now()},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now(), "onupdate": sa.func.now()},
    )

    users: List["User"] = Relationship(
        back_populates="company", sa_relationship_kwargs={"foreign_keys": "[User.company_id]"}
    )
    areas: List["Area"] = Relationship(
        back_populates="company", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    audit_assignments: List["AuditAssignment"] = Relationship(back_populates="company")


# Base model for shared Area fields
class AreaBase(SQLModel):
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)


# Database model for Area
class Area(AreaBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    company_id: uuid.UUID = Field(foreign_key="company.id")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now()},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now(), "onupdate": sa.func.now()},
    )

    company: "Company" = Relationship(back_populates="areas")
    user_links: List["UserAreaAssignmentLink"] = Relationship(
        back_populates="area", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    audit_assignments: List["AuditAssignment"] = Relationship(back_populates="area")

    __table_args__ = (sa.UniqueConstraint("name", "company_id", name="uq_area_name_company_id"),)


# Base model for shared AuditTemplate fields
class AuditTemplateBase(SQLModel):
    name: str = Field(unique=True, max_length=255)
    description: Optional[str] = Field(default=None)
    audit_type_definition_key: str = Field(max_length=255)


# Database model for AuditTemplate
class AuditTemplate(AuditTemplateBase, table=True):
    __tablename__ = "audit_template"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_by_id: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now()},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now(), "onupdate": sa.func.now()},
    )

    created_by: "User" = Relationship(back_populates="audit_templates_created")
    question_templates: List["QuestionTemplate"] = Relationship(
        back_populates="audit_template", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    audit_assignments: List["AuditAssignment"] = Relationship(back_populates="audit_template")


# Base model for shared QuestionTemplate fields
class QuestionTemplateBase(SQLModel):
    text: str
    question_type: QuestionType = Field(sa_column=sa.Column(sa.Enum(QuestionType)))
    options: Optional[Any] = Field(default=None, sa_column=sa.Column(postgresql.JSONB))
    order: int
    is_mandatory: bool = Field(default=True)
    section_id: Optional[str] = Field(default=None, max_length=255)
    scoring_weight: Optional[float] = Field(default=None)


# Database model for QuestionTemplate
class QuestionTemplate(QuestionTemplateBase, table=True):
    __tablename__ = "question_template"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    audit_template_id: uuid.UUID = Field(foreign_key="audit_template.id")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now()},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now(), "onupdate": sa.func.now()},
    )

    audit_template: "AuditTemplate" = Relationship(back_populates="question_templates")


# Base model for shared AuditAssignment fields
class AuditAssignmentBase(SQLModel):
    title: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    due_date: Optional[datetime] = Field(default=None)
    status: AuditAssignmentStatus = Field(
        default=AuditAssignmentStatus.PENDING, sa_column=sa.Column(sa.Enum(AuditAssignmentStatus))
    )
    periodicity: Optional[AuditPeriodicity] = Field(
        default=None, sa_column=sa.Column(sa.Enum(AuditPeriodicity))
    )
    next_due_date: Optional[date] = Field(default=None)
    is_public: bool = Field(default=False)


# Database model for AuditAssignment
class AuditAssignment(AuditAssignmentBase, table=True):
    __tablename__ = "audit_assignment"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    audit_template_id: uuid.UUID = Field(foreign_key="audit_template.id")
    company_id: uuid.UUID = Field(foreign_key="company.id")
    area_id: Optional[uuid.UUID] = Field(default=None, foreign_key="area.id")
    created_by_id: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now()},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now(), "onupdate": sa.func.now()},
    )

    audit_template: "AuditTemplate" = Relationship(back_populates="audit_assignments")
    company: "Company" = Relationship(back_populates="audit_assignments")
    area: Optional["Area"] = Relationship(back_populates="audit_assignments")
    created_by: "User" = Relationship(back_populates="audit_assignments_created")
    assigned_questions: List["AssignedQuestion"] = Relationship(
        back_populates="audit_assignment", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    audit_responses: List["AuditResponse"] = Relationship(
        back_populates="audit_assignment", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


# Base model for shared AssignedQuestion fields
class AssignedQuestionBase(SQLModel):
    text: str
    question_type: QuestionType = Field(sa_column=sa.Column(sa.Enum(QuestionType)))
    options: Optional[Any] = Field(default=None, sa_column=sa.Column(postgresql.JSONB))
    order: int
    is_mandatory: bool
    section_id: Optional[str] = Field(default=None, max_length=255)
    scoring_weight: Optional[float] = Field(default=None)


# Database model for AssignedQuestion
class AssignedQuestion(AssignedQuestionBase, table=True):
    __tablename__ = "assigned_question"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    audit_assignment_id: uuid.UUID = Field(foreign_key="audit_assignment.id")
    original_question_template_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="question_template.id"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now()},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now(), "onupdate": sa.func.now()},
    )

    audit_assignment: "AuditAssignment" = Relationship(back_populates="assigned_questions")
    original_question_template: Optional["QuestionTemplate"] = Relationship()
    answers: List["Answer"] = Relationship(back_populates="assigned_question")


# Base model for shared AuditResponse fields
class AuditResponseBase(SQLModel):
    overall_comments: Optional[str] = Field(default=None)
    photo_urls: Optional[List[str]] = Field(default=None, sa_column=sa.Column(postgresql.JSONB))
    status: AuditResponseStatus = Field(
        default=AuditResponseStatus.DRAFT, sa_column=sa.Column(sa.Enum(AuditResponseStatus))
    )
    score: Optional[float] = Field(default=None)


# Database model for AuditResponse
class AuditResponse(AuditResponseBase, table=True):
    __tablename__ = "audit_response"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    audit_assignment_id: uuid.UUID = Field(foreign_key="audit_assignment.id")
    auditor_id: uuid.UUID = Field(foreign_key="user.id")
    submission_date: Optional[datetime] = Field(default=None)

    audit_assignment: "AuditAssignment" = Relationship(back_populates="audit_responses")
    auditor: "User" = Relationship(back_populates="audit_responses")
    answers: List["Answer"] = Relationship(
        back_populates="audit_response", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


# Base model for shared Answer fields
class AnswerBase(SQLModel):
    answer_value: Optional[Any] = Field(default=None, sa_column=sa.Column(postgresql.JSONB))
    comments: Optional[str] = Field(default=None)
    photo_urls: Optional[List[str]] = Field(default=None, sa_column=sa.Column(postgresql.JSONB))


# Database model for Answer
class Answer(AnswerBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    audit_response_id: uuid.UUID = Field(foreign_key="audit_response.id")
    assigned_question_id: uuid.UUID = Field(foreign_key="assigned_question.id")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now()},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": sa.func.now(), "onupdate": sa.func.now()},
    )

    audit_response: "AuditResponse" = Relationship(back_populates="answers")
    assigned_question: "AssignedQuestion" = Relationship(back_populates="answers")





# User models
class UserCreate(UserBase):
    password: str

    @model_validator(mode='after')
    def check_company_id_for_role(self) -> 'UserCreate':
        if self.role in (UserRole.USER, UserRole.AUDITOR) and not self.company_id:
            raise ValueError("company_id is required for USER and AUDITOR roles")
        return self


class UserUpdate(SQLModel):
    email: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role: Optional[UserRole] = None
    is_verified: Optional[bool] = None
    company_id: Optional[uuid.UUID] = None


class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime


class UsersPublic(SQLModel):
    data: List[UserPublic]
    count: int


# Company models
class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(SQLModel):
    name: Optional[str] = None
    details: Optional[str] = None
    is_demo: Optional[bool] = None


class CompanyPublic(CompanyBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CompaniesPublic(SQLModel):
    data: List[CompanyPublic]
    count: int


# Area models
class AreaCreate(AreaBase):
    pass


class AreaUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None


class AreaPublic(AreaBase):
    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class AreasPublic(SQLModel):
    data: List[AreaPublic]
    count: int


# AuditTemplate models
class QuestionTemplatePublic(QuestionTemplateBase):
    id: uuid.UUID
    audit_template_id: uuid.UUID


class AuditTemplateCreate(AuditTemplateBase):
    pass


class AuditTemplateUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None


class AuditTemplatePublic(AuditTemplateBase):
    id: uuid.UUID
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    question_templates: List[QuestionTemplatePublic] = []


class AuditTemplatesPublic(SQLModel):
    data: List[AuditTemplatePublic]
    count: int


# QuestionTemplate models
class QuestionTemplateCreate(QuestionTemplateBase):
    audit_template_id: uuid.UUID


class QuestionTemplateUpdate(SQLModel):
    text: Optional[str] = None
    question_type: Optional[QuestionType] = None
    options: Optional[Any] = None
    order: Optional[int] = None
    is_mandatory: Optional[bool] = None
    section_id: Optional[str] = None
    scoring_weight: Optional[float] = None


class QuestionTemplatesPublic(SQLModel):
    data: List[QuestionTemplatePublic]
    count: int


# AssignedQuestion models
class AssignedQuestionPublic(AssignedQuestionBase):
    id: uuid.UUID
    audit_assignment_id: uuid.UUID
    original_question_template_id: Optional[uuid.UUID] = None


# AuditAssignment models
class AuditAssignmentCreate(AuditAssignmentBase):
    audit_template_id: uuid.UUID
    company_id: uuid.UUID
    area_id: Optional[uuid.UUID] = None


class AuditAssignmentUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[AuditAssignmentStatus] = None
    periodicity: Optional[AuditPeriodicity] = None
    next_due_date: Optional[date] = None
    area_id: Optional[uuid.UUID] = None
    is_public: Optional[bool] = None


class AuditAssignmentPublic(AuditAssignmentBase):
    id: uuid.UUID
    audit_template_id: uuid.UUID
    company_id: uuid.UUID
    area_id: Optional[uuid.UUID] = None
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    audit_template: Optional[AuditTemplatePublic] = None
    assigned_questions: List[AssignedQuestionPublic] = []


class AuditAssignmentsPublic(SQLModel):
    data: List[AuditAssignmentPublic]
    count: int


# AssignedQuestion models
class AssignedQuestionCreate(AssignedQuestionBase):
    audit_assignment_id: uuid.UUID
    original_question_template_id: Optional[uuid.UUID] = None


class AssignedQuestionUpdate(SQLModel):
    text: Optional[str] = None
    options: Optional[Any] = None
    order: Optional[int] = None
    is_mandatory: Optional[bool] = None
    section_id: Optional[str] = None


class AssignedQuestionsPublic(SQLModel):
    data: List[AssignedQuestionPublic]
    count: int


# Answer models
class AnswerCreate(AnswerBase):
    assigned_question_id: uuid.UUID


class AnswerUpdate(SQLModel):
    answer_value: Optional[Any] = None
    comments: Optional[str] = None
    photo_urls: Optional[List[str]] = None


class AnswerPublic(AnswerBase):
    id: uuid.UUID
    audit_response_id: uuid.UUID
    assigned_question_id: uuid.UUID


# AuditResponse models
class AuditResponseCreate(AuditResponseBase):
    audit_assignment_id: uuid.UUID
    answers: Optional[List[AnswerCreate]] = []


class AuditResponseUpdate(SQLModel):
    overall_comments: Optional[str] = None
    photo_urls: Optional[List[str]] = None
    status: Optional[AuditResponseStatus] = None
    score: Optional[float] = None


class AuditResponsePublic(AuditResponseBase):
    id: uuid.UUID
    audit_assignment_id: uuid.UUID
    auditor_id: uuid.UUID
    submission_date: Optional[datetime]
    answers: List[AnswerPublic] = []


class AuditResponsesPublic(SQLModel):
    data: List[AuditResponsePublic]
    count: int


# Update forward references to resolve circular dependencies
AuditTemplatePublic.model_rebuild()
AuditAssignmentPublic.model_rebuild()
