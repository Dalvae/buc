# Web Application Architecture

## 1. Introduction

This document outlines the backend architecture for a web application designed for managing companies, users, and conducting audits. The backend will be built using FastAPI and SQLModel, while the frontend will be a React application that adapts to the backend API.

The existing `items` model and related functionalities from the base template will be removed and are not considered part of this architecture.

## 2. User Roles and Permissions

The application will feature a hierarchical role-based access control system.

- **Superuser**:

  - Inherits all permissions from the base template.
  - Top-level administrative access.
  - Can manage Administrators.
  - Likely responsible for system-wide configurations.

- **Administrator**:

  - Managed by Superusers.
  - Possesses broad permissions to manage all aspects of the system, including all Companies, Users, and audit-related entities, irrespective of any primary company affiliation they might have via their `User.company_id`.
  - Can create and manage other Administrators, Auditors, and Users.
  - Can verify Users (transitioning them from `is_verified = False` to `is_verified = True`, enabling broader system access).
  - Can create and manage Companies.
  - Can create and manage Areas within Companies.
  - Can assign Users and Auditors to specific Areas.
  - Can create, edit, and manage Audit Templates.
  - Can create Audit Assignments for companies and assign them to Auditors.
  - Can view all audit responses.

- **Auditor**:

  - A type of verified User.
  - Assigned to one Company and one or more Areas within that Company.
  - Can view data for their assigned Company and Area(s).
  - Can view and respond to Audit Assignments assigned to them within their designated Areas.

- **User (Verified User)**:

  - Account has `is_verified = True` (set by an Administrator).
  - Associated with a primary Company (via `company_id`) and one or more Areas within that company.
  - Can view data related to their associated Company and assigned Area(s). Specific data access will depend on further business rules. Data outside their assigned scope (Company/Area) is not visible.

- **Unverified User**:

  - Account has `is_verified = False`.
  - Any user who has registered but not yet been verified by an Administrator, or a user whose verification has been revoked.
  - Limited access, primarily to their own profile and the ability to request verification or see basic public information (if any). Cannot access company-specific data or functionalities.

- **Demo Company Interaction**:
  - A special "Demo Company" will exist.
  - Any user (Verified User, Auditor) interacting with the Demo Company will effectively operate with Auditor-like permissions _within the scope of the Demo Company_.
  - Sensitive data (e.g., user emails, full names) associated with the Demo Company will be obfuscated when viewed by users who are not Superusers or Administrators.

## 3. Core Entities (Backend SQLModel Models)

### 3.1. User (`user`)

- Extends the existing `User` model from the template.
- `id` (UUID, Primary Key)
- `email` (String, Unique, Indexed)
- `hashed_password` (String)
- `full_name` (String, Optional)
- `is_active` (Boolean, default: True) - Indicates if the user account is enabled and can log in.
- `is_superuser` (Boolean, default: False) - This will identify the **Superuser**.
- `role` (Enum: ADMIN, AUDITOR, USER, default: USER) - Defines the primary role.
- `is_verified` (Boolean, default: False) - Indicates if the user's identity and role have been confirmed by an Administrator. Unverified users (even if `is_active`) have very limited access. Verification is typically required for Users and Auditors to access company-specific data.
- `company_id` (UUID, ForeignKey to `company.id`, Optional) - Primary company association. For `USER` and `AUDITOR` roles, this typically defines their main operational scope. For `ADMINISTRATOR` and `SUPERUSER` roles, this field may be `NULL` or set to a specific company, but it does not restrict their ability to manage all companies as per their role permissions.
- `created_at` (DateTime)
- `updated_at` (DateTime)
- _Relationships_:
  - `company` (Optional, to Company) - Primary company.
  - `assigned_areas` (List of `Area` through `UserAreaAssignmentLink`) - Areas the user has access to.
  - `audit_assignments_created` (List of AuditAssignment, as creator)
  - `audit_responses` (List of AuditResponse, as responder)
  - `audit_templates_created` (List of AuditTemplate, as creator)

### 3.2. Company (`company`)

- `id` (UUID, Primary Key)
- `name` (String, Unique)
- `details` (String, Optional, e.g., address, contact info)
- `is_demo` (Boolean, default: False) - Flag for special handling of data (e.g., obfuscation, auditor-like access for users).
- `created_at` (DateTime)
- `updated_at` (DateTime)
- _Relationships_:
  - `users` (List of User, representing primary association)
  - `areas` (List of Area, cascade delete)
  - `audit_assignments` (List of AuditAssignment)

### 3.3. Area (`area`)

    - Represents a functional or physical area within a company (e.g., "Production Line A", "Security Department", "Warehouse Section 1").
    - `id` (UUID, Primary Key)
    - `name` (String) - Must be unique within the company.
    - `description` (String, Optional)
    - `company_id` (UUID, ForeignKey to `company.id`)
    - `created_at` (DateTime)
    - `updated_at` (DateTime)
    - *Relationships*:
        - `company` (to Company)
        - `user_assignments` (List of `UserAreaAssignmentLink`, for M:N with User)
        - `audit_assignments` (List of `AuditAssignment`, if audits are area-specific)

### 3.4. UserAreaAssignmentLink (`user_area_assignment_link`) - Association Table

    - Links Users to specific Areas they are authorized to access or audit.
    - `user_id` (UUID, ForeignKey to `user.id`, Primary Key)
    - `area_id` (UUID, ForeignKey to `area.id`, Primary Key)
    - `assigned_at` (DateTime, default: now)
    - *Relationships*:
        - `user` (to User)
        - `area` (to Area)

### 3.5. Audit Template (`audit_template`)

- Represents a user-customized template for an audit, derived from a code-defined `AuditTypeDefinition` (see section below).
- `id` (UUID, Primary Key)
- `name` (String, Unique within a user/company context if necessary, or globally unique)
- `description` (String, Optional)
- `audit_type_definition_key` (String) - Key referencing a code-defined audit type (e.g., "5S_AUDIT", "SECURITY_CHECKLIST").
- `created_by_id` (UUID, ForeignKey to `user.id` - Admin/Superuser)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- _Relationships_:
  - `question_templates` (List of QuestionTemplate, cascade delete)
  - `audit_assignments` (List of AuditAssignment)
  - `created_by` (to User)

### 3.6. Question Template (`question_template`)

- Represents a question within an Audit Template. Its structure and validation rules are influenced by the parent `AuditTemplate`'s `audit_type_definition_key`.
- `id` (UUID, Primary Key)
- `audit_template_id` (UUID, ForeignKey to `audit_template.id`)
- `text` (String) - The question itself.
- `question_type` (Enum: TEXT, MULTIPLE_CHOICE_SINGLE, MULTIPLE_CHOICE_MULTIPLE, YES_NO, RATING_SCALE, SECTION_HEADER, etc.) - Defined by the audit type.
- `options` (JSON, Optional) - For multiple choice, rating scale definitions, etc. Structure depends on `question_type`.
- `order` (Integer) - To maintain question order within a template.
- `is_mandatory` (Boolean, default: True)
- `section_id` (String, Optional) - For grouping questions into sections, if supported by the audit type.
- `scoring_weight` (Float, Optional) - If applicable to the audit type.
- `created_at` (DateTime)
- `updated_at` (DateTime)
- _Relationships_:
  - `audit_template` (to AuditTemplate)

### 3.7. Audit Assignment (`audit_assignment`)

- An instance of an audit (derived from a template) assigned to a specific company or area.
- `id` (UUID, Primary Key)
- `audit_template_id` (UUID, ForeignKey to `audit_template.id`) - Link to the original template.
- `company_id` (UUID, ForeignKey to `company.id`)
- `area_id` (UUID, ForeignKey to `area.id`, Optional) - Specifies the area within the company for this audit. If NULL, it's a company-wide assignment.
- `title` (String) - Can be derived from template name + company name, or custom.
- `description` (String, Optional)
- `due_date` (DateTime, Optional)
- `is_public` (Boolean, default: False) - If `True`, the assignment is visible to all verified users within the same company, regardless of their area assignments.
- `status` (Enum: PENDING, IN_PROGRESS, COMPLETED, OVERDUE, default: PENDING)
- `periodicity` (Enum: ONE_TIME, DAILY, WEEKLY, MONTHLY, QUARTERLY, ANNUALLY, Optional)
- `next_due_date` (Date, Optional) - Calculated based on periodicity and completion date.
- `created_by_id` (UUID, ForeignKey to `user.id` - Admin/Superuser)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- _Relationships_:
  - `audit_template` (to AuditTemplate)
  - `company` (to Company)
  - `area` (Optional, to Area)
  - `assigned_questions` (List of AssignedQuestion, cascade delete)
  - `audit_responses` (List of AuditResponse, cascade delete)
  - `created_by` (to User)

### 3.8. Assigned Question (`assigned_question`)

- A specific question as part of an Audit Assignment. This allows for modifications from the original template for a particular assignment (e.g., slight rephrasing, making a question optional for one assignment).
- `id` (UUID, Primary Key)
- `audit_assignment_id` (UUID, ForeignKey to `audit_assignment.id`)
- `original_question_template_id` (UUID, ForeignKey to `question_template.id`, Optional) - To trace back to the template.
- `text` (String) - Copied from QuestionTemplate, can be overridden by Admin during assignment creation/editing.
- `question_type` (Enum) - Copied from QuestionTemplate.
- `options` (JSON, Optional) - Copied from QuestionTemplate, can be overridden.
- `order` (Integer) - Order within this specific assignment.
- `is_mandatory` (Boolean) - Copied from QuestionTemplate, can be overridden.
- `section_id` (String, Optional) - Copied from QuestionTemplate.
- `created_at` (DateTime)
- `updated_at` (DateTime)
- _Relationships_:
  - `audit_assignment` (to AuditAssignment)
  - `original_question_template` (Optional, to QuestionTemplate)
  - `answers` (List of Answer)

### 3.9. Audit Response (`audit_response`)

- Represents a single submission of an audit by an Auditor.
- `id` (UUID, Primary Key)
- `audit_assignment_id` (UUID, ForeignKey to `audit_assignment.id`)
- `auditor_id` (UUID, ForeignKey to `user.id` - Auditor who submitted)
- `submission_date` (DateTime, default: now)
- `overall_comments` (String, Optional)
- `photo_urls` (list[str] | None = Field(default=None, sa_column=sa.Column(postgresql.JSONB))) - URLs of photos attached to the overall response.
- `status` (Enum: DRAFT, SUBMITTED, default: DRAFT)
- `score` (Float, Optional) - Calculated score based on answers and audit type definition.
- _Relationships_:
  - `audit_assignment` (to AuditAssignment)
  - `auditor` (to User)
  - `answers` (List of Answer, cascade delete)

### 3.10. Answer (`answer`)

- An answer to a specific AssignedQuestion within an AuditResponse.
- `id` (UUID, Primary Key)
- `audit_response_id` (UUID, ForeignKey to `audit_response.id`)
- `assigned_question_id` (UUID, ForeignKey to `assigned_question.id`)
- `answer_value` (String/JSON) - Flexible field to store the answer based on `question_type`.
- `comments` (String, Optional) - Auditor's comments for this specific answer.
- `photo_urls` (list[str] | None = Field(default=None, sa_column=sa.Column(postgresql.JSONB))) - URLs of photos attached to this specific answer.
- `created_at` (DateTime)
- `updated_at` (DateTime)
- _Relationships_:
  - `audit_response` (to AuditResponse)
  - `assigned_question` (to AssignedQuestion)

## 4. Code-Defined Audit Types (AuditTypeDefinition)

To support varied audit structures (e.g., "5S" with sections and 1-5 scales, "Security" with boolean checklists) and custom scoring logic, audit types will be defined in Python code within the backend.

- **Location**: A dedicated Python module, e.g., `backend/app/audit_types/`.
- **Database Migrations**: The `AuditTypeDefinition` classes themselves are code and do not directly require database migrations. However, the `AuditTemplate` model, which stores the `audit_type_definition_key` to link to these definitions, will require a migration if this field or related logic changes.
- **Structure**:

  - An abstract base class (e.g., `AuditTypeDefinitionBase`) will define a common interface. This interface might include methods for:
    - `get_key()`: Returns the unique string key.
    - `get_name()`: Returns a human-readable name for the audit type.
    - `get_default_sections()`: Returns a list of default section definitions (if applicable).
    - `get_allowed_question_types()`: Returns a list of `QuestionType` enums valid for this audit type.
    - `validate_question(question_template: QuestionTemplate)`: Validates a question against the audit type's rules.
    - `calculate_score(audit_response: AuditResponse)`: Calculates the score for a completed audit.
  - Concrete classes (e.g., `FiveSAuditType`, `SecurityChecklistAuditType`) will inherit from `AuditTypeDefinitionBase` and implement its methods.
  - Each concrete class will define:
    - **Unique Key**: A string identifier (e.g., "FIVE_S_AUDIT", "SECURITY_CHECKLIST_AUDIT"). This key is stored in `AuditTemplate.audit_type_definition_key`.
    - **Question Structure**: Defines the typical structure, including:
      - Whether it uses sections.
      - Allowed `QuestionType` enums (e.g., RATING_SCALE, YES_NO, TEXT).
      - Default options for question types (e.g., rating scale from 1 to 5).
    - **Validation Logic**: Methods to validate `QuestionTemplate` instances created by an Admin for an `AuditTemplate` of this type.
    - **Scoring Logic**: Methods to calculate a score for an `AuditResponse` based on its `Answers`. This logic is specific to the audit type.

- **Example Audit Type Definitions**:

  - **`FiveSAuditType` (5S Audit)**:

    - `key`: "FIVE_S_AUDIT"
    - `name`: "5S Audit"
    - `default_sections`:
      - `Sort` (Seiri)
      - `Set in Order` (Seiton)
      - `Shine` (Seiso)
      - `Standardize` (Seiketsu)
      - `Sustain` (Shitsuke)
    - `allowed_question_types`: Primarily `RATING_SCALE` (e.g., 1-5 points), `TEXT` (for comments).
    - `scoring_logic`: Could be a sum of ratings for all questions, potentially weighted per section or question. The result might be a raw score and/or a percentage.

  - **`SecurityChecklistAuditType` (Security Checklist Audit)**:
    - `key`: "SECURITY_CHECKLIST_AUDIT"
    - `name`: "Security Checklist Audit"
    - `default_sections`: Optional, could be e.g., "Physical Security", "Access Control", "Data Security".
    - `allowed_question_types`: Primarily `YES_NO`, `TEXT` (for findings/comments).
    - `scoring_logic`: Could be a count of "Yes" answers, a percentage of compliance, or a risk-based score.

- **Admin Interface**: When an Administrator creates an `AuditTemplate`, they would select from a list of available code-defined audit types (discovered by the system from the `backend/app/audit_types/` module). The system then uses the selected `AuditTypeDefinition` to:

  - Suggest default sections and questions.
  - Guide the creation and validation of `QuestionTemplate`s within that `AuditTemplate`.
  - Determine how to score `AuditResponse`s associated with assignments from this template.

- **Extensibility**: New audit types can be added by creating new Python classes inheriting from `AuditTypeDefinitionBase` in the `backend/app/audit_types/` module. This makes the system extensible for new audit methodologies without requiring database schema changes for the definition of each new audit structure itself.

## 5. Key Backend API Endpoints (High-Level Overview)

This is not an exhaustive list but covers the main resource interactions. Standard CRUD operations (Create, Read, Update, Delete) are implied unless specified.

- **Authentication (`/api/v1/login`, `/api/v1/users/me`, etc.)**

  - Leverage existing endpoints from the template.
  - Enhance `/api/v1/users/me` to return role and company information.

- **Users (`/api/v1/users`)**

  - `POST /signup`: Public user registration (creates Unverified User).
  - `GET /`: List users (Admin/Superuser).
  - `POST /`: Create user (Admin/Superuser).
  - `GET /{user_id}`: Get user details (Admin/Superuser, or self).
  - `PATCH /{user_id}`: Update user (Admin/Superuser, or self for limited fields).
    - Includes role changes, company assignment, Area assignments by Admin/Superuser.
  - `DELETE /{user_id}`: Delete user (Admin/Superuser).
  - `POST /{user_id}/verify`: Verify a user (Admin/Superuser).
  - `POST /{user_id}/assign-role`: Assign/change role (Admin/Superuser).
  - `POST /{user_id}/assign-areas`: Assign user (including Auditors and regular Users) to specific Areas within their primary Company (Admin/Superuser).

- **Companies (`/api/v1/companies`)**

  - `GET /`: List companies (Admin/Superuser, Users/Auditors see their own or based on permissions).
  - `POST /`: Create company (Admin/Superuser).
  - `GET /{company_id}`: Get company details.
  - `PATCH /{company_id}`: Update company (Admin/Superuser).
  - `DELETE /{company_id}`: Delete company (Admin/Superuser).

- **Areas (`/api/v1/companies/{company_id}/areas`)**

  - `GET /`: List areas for a company.
  - `POST /`: Create an area within a company (Admin/Superuser).
  - `GET /{area_id}`: Get area details.
  - `PATCH /{area_id}`: Update area (Admin/Superuser).
  - `DELETE /{area_id}`: Delete area (Admin/Superuser).

- **Audit Templates (`/api/v1/audit-templates`)**

  - `GET /`: List audit templates (Admin/Superuser, Auditors might see list for selection).
  - `GET /types`: List available code-defined audit type definitions (e.g., "5S_AUDIT", "SECURITY_CHECKLIST") for Admins to choose from when creating a template.
  - `POST /`: Create audit template (Admin/Superuser), requires specifying an `audit_type_definition_key`.
  - `GET /{template_id}`: Get audit template details.
  - `PATCH /{template_id}`: Update audit template (Admin/Superuser).
  - `DELETE /{template_id}`: Delete audit template (Admin/Superuser).

- **Question Templates (`/api/v1/audit-templates/{template_id}/questions`)**

  - `GET /`: List questions for a template (Admin/Superuser).
  - `POST /`: Add question to template (Admin/Superuser). Validation against the template's `AuditTypeDefinition`.
  - `GET /{question_id}`: Get question details.
  - `PATCH /{question_id}`: Update question (Admin/Superuser).
  - `DELETE /{question_id}`: Remove question from template (Admin/Superuser).

- **Audit Assignments (`/api/v1/audit-assignments`)**

  - `GET /`: List all assignments (Admin/Superuser).
  - `GET /my-assignments`: List assignments the logged-in Auditor can respond to (based on their company and area assignments).
  - `GET /company/{company_id}`: List assignments for a specific company (Admin/Superuser, relevant Users/Auditors based on new visibility rules).
  - `POST /`: Create audit assignment from a template for a company or area (Admin/Superuser).
    - This endpoint will handle copying/linking questions from the template to `AssignedQuestion` instances.
    - No longer assigns to a specific auditor.
  - `GET /{assignment_id}`: Get assignment details including its questions.
  - `PATCH /{assignment_id}`: Update assignment details (e.g., due date, area, status by Admin). `assigned_to_auditor_id` is removed.
  - `DELETE /{assignment_id}`: Delete assignment (Admin/Superuser).

- **Audit Responses (`/api/v1/audit-assignments/{assignment_id}/responses`)**
  - `GET /`: List responses for an assignment (Admin/Superuser, users who can access the assignment).
  - `POST /`: Create/Submit an audit response (Auditor who can respond to the AuditAssignment based on company/area).
    - This will involve submitting answers to all `AssignedQuestion`s.
    - Score calculation will be triggered based on the audit type definition.
  - `GET /{response_id}`: Get specific audit response details including all answers and score.
  - `PATCH /{response_id}`: Update a draft audit response (Auditor).

## 6. Data Obfuscation for Demo Company

For any `Company` where `is_demo` is true, sensitive data needs to be obfuscated when displayed or retrieved via the API by users who are not Superusers or Administrators. This primarily applies to:
_ User emails and full names associated with the demo company.
_ Potentially other PII within audit responses or company/area details if applicable.

**Strategy**:

- **Backend Logic**: Implement obfuscation at the Pydantic model serialization level (e.g., using custom serializers or `@computed_field` in `UserPublic` and other relevant models). This logic will check if the data pertains to a demo company and if the requesting user has sufficient privileges (Superuser/Admin) to see unobfuscated data.
- API endpoints returning lists of users or company-related data will need to apply this logic consistently.

## 7. Key Model Relationships Summary

- A **User** has a primary association with one **Company**.
- A **User** can be assigned to multiple **Areas** (via `UserAreaAssignmentLink`), typically within their primary company or companies they audit.
- A **Company** can have many **Users** (primary association) and many **Areas**.
- An **Area** belongs to one **Company** and can have many **Users** assigned to it.
- An **AuditTemplate** is created by a **User** (Admin/Superuser) and is based on a code-defined `AuditTypeDefinition` (identified by `audit_type_definition_key`).
- An **AuditTemplate** has many **QuestionTemplates**.
- An **AuditAssignment** is based on one **AuditTemplate**, assigned to one **Company**, and optionally one **Area**. It's created by an **Admin/Superuser**. (No longer assigned to a specific Auditor).
- An **AuditAssignment** has many **AssignedQuestions** (derived/copied from QuestionTemplates).
- An **AuditResponse** belongs to one **AuditAssignment** and is submitted by one **Auditor** (who has permission to respond based on company/area). It may have a calculated `score`.
- An **AuditResponse** has many **Answers**.
- An **Answer** belongs to one **AssignedQuestion** within an AuditResponse.

This architecture provides a flexible foundation. Details for specific fields, validation rules, and more granular API endpoint logic will be refined during development.
