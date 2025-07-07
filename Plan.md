# Backend Refinement and Optimization Plan

This document outlines the remaining tasks to refine, optimize, and secure the backend implementation based on the architecture defined in `architecture.md`. The initial model and endpoint implementation is complete; this plan focuses on critical logic, performance, and security enhancements.

---

### Task 1: (High Priority) Optimize Database Queries to Prevent "N+1" Problem

**Description**:
Many API endpoints that return lists of objects with relationships (e.g., audit assignments with their templates, responses with their answers) are likely performing an excessive number of database queries, leading to poor performance. This task is to identify and fix these "N+1" query issues by using eager loading.

**Action Plan**:
1.  **Identify Problematic Endpoints**: Review all `GET` endpoints that return lists of objects in `backend/app/api/routes/`. Pay special attention to those that return nested `*Public` models, such as:
    *   `GET /api/v1/audit-assignments/`
    *   `GET /api/v1/audit-responses/`
    *   `GET /api/v1/users/`
    *   `GET /api/v1/companies/`
2.  **Implement Eager Loading**:
    *   Modify the corresponding functions in `backend/app/crud.py` (e.g., `get_multi` methods).
    *   Use `sqlalchemy.orm.selectinload` in the `select()` statements to tell SQLAlchemy to fetch related objects in a single, efficient query.
    *   **Example for Audit Assignments**:
        ```python
        # In backend/app/crud.py, inside a function returning multiple assignments
        from sqlalchemy.orm import selectinload
        
        statement = select(models.AuditAssignment).options(
            selectinload(models.AuditAssignment.audit_template),
            selectinload(models.AuditAssignment.assigned_questions)
        )
        ```
3.  **Verify**: Use logging or a profiler to confirm that the number of queries executed per request has been reduced significantly.

**Primary Files**:
*   `backend/app/crud.py`
*   All files in `backend/app/api/routes/`

---

### Task 2: Implement Critical Business Logic

**Description**:
Two key pieces of business logic from the architecture are not yet implemented: setting the `submission_date` for audit responses and obfuscating data for the demo company.

**Action Plan**:

**A. Set `submission_date` on Audit Completion**:
1.  **Locate the Endpoint**: Identify the API endpoint responsible for updating an `AuditResponse`, likely `PATCH /api/v1/audit-assignments/{...}/responses/{response_id}` in `backend/app/api/routes/audit_responses.py`.
2.  **Implement Logic**:
    *   In the update logic, check if the incoming payload is changing the `status` to `AuditResponseStatus.SUBMITTED`.
    *   If it is, and the existing `audit_response.submission_date` in the database is `None`, set `audit_response.submission_date = datetime.utcnow()`.
    *   Save the updated object.

**B. Implement Data Obfuscation for Demo Company**:
1.  **Identify Sensitive Endpoints**: Find all endpoints that return user information or other potentially sensitive data related to a company. This includes:
    *   `GET /api/v1/users/{user_id}`
    *   `GET /api/v1/companies/{company_id}` (if it includes user lists)
    *   Endpoints returning `AuditResponsePublic` or `AuditAssignmentPublic` which might contain `created_by` user details.
2.  **Create a Utility Function**: It's best to create a helper function, e.g., `obfuscate_data_for_demo_company(data, current_user)`, in `backend/app/api/deps.py` or a new `utils.py`.
3.  **Implement Obfuscation Logic**:
    *   The function should take the data to be returned (e.g., a `UserPublic` object or a list of them) and the currently authenticated user.
    *   It will check if the data belongs to a demo company and if the `current_user` is **not** an `ADMIN` or `SUPERUSER`.
    *   If both are true, it modifies the data in-place or returns a new, obfuscated copy (e.g., `user.email = "hidden"`, `user.full_name = "Demo User"`).
4.  **Apply in Endpoints**: Call this utility function just before returning the response from the identified endpoints.

**Primary Files**:
*   `backend/app/api/routes/audit_responses.py`
*   `backend/app/api/routes/users.py`
*   `backend/app/api/routes/companies.py`
*   `backend/app/api/deps.py` (or a new utility file)

---

### Task 3: (Security) Comprehensive Endpoint Permission and Scope Review

**Description**:
Ensure that every API endpoint is protected by the correct permission checks and that data access is properly scoped to the user's role and company/area assignments.

**Action Plan**:
1.  **Review All Endpoints**: Go through every single path operation in all files under `backend/app/api/routes/`.
2.  **Verify Dependencies**: For each endpoint, ensure it has the appropriate dependency injectors from `backend/app/api/deps.py`:
    *   `get_current_active_superuser` for superuser-only actions.
    *   A dependency for "Admin" role checks.
    *   `get_current_active_user` for any authenticated user.
3.  **Check Data Scoping**: For endpoints that return or modify a specific object (e.g., `GET /api/v1/companies/{company_id}`), verify that there is logic to check if the user has the right to access *that specific object*.
    *   A regular user should not be able to access a company they don't belong to.
    *   An auditor should only see audits for their assigned areas (unless the audit is public within the company).
4.  **Add Missing Checks**: Implement any missing permission or scope checks. This might involve creating new, more specific dependency injectors (e.g., a dependency that validates a user has access to a specific `company_id` provided in the path).

**Primary Files**:
*   All files in `backend/app/api/routes/`
*   `backend/app/api/deps.py`
*   `backend/app/crud.py` (to add scope filters to queries)

---

### Task 4: Refactor and Verify Core Audit System Logic

**Description**:
The logic connecting code-defined `AuditTypeDefinition` with database models (`AuditTemplate`, `AuditAssignment`) is complex and critical. This task is to refactor and explicitly verify this entire workflow, from template creation to score calculation.

**Action Plan**:

**A. Implement a Registry for Audit Types**:
1.  **Create a Factory/Registry**: In `backend/app/audit_types/__init__.py`, create a simple registry (e.g., a dictionary) that automatically discovers and maps `audit_type_definition_key` strings to their corresponding `AuditTypeDefinition` classes.
2.  **Refactor Logic**: Any code that needs to access a definition class should use this registry instead of manual lookups. This centralizes the logic.

**B. Solidify the Audit Assignment Creation Process**:
1.  **Review Endpoint**: Deeply review `POST /api/v1/audit-assignments`.
2.  **Confirm Copy Logic**: Ensure the endpoint is correctly **copying** `QuestionTemplate` records into new `AssignedQuestion` records. It must not simply link to the original template's questions.
3.  **Add Tests**: Write specific unit or integration tests that prove that editing an `AuditTemplate` *after* an `AuditAssignment` has been created from it *does not* change the assigned questions.

**C. Implement and Test Score Calculation**:
1.  **Triggering Logic**: In the endpoint that handles audit submission (`PATCH` on an `AuditResponse` changing status to `SUBMITTED`), add the logic to trigger the score calculation.
2.  **Calculation Flow**: The logic must:
    *   Fetch the `AuditResponse` and its parent `AuditAssignment` and `AuditTemplate`.
    *   Use the `audit_type_definition_key` from the template to get the correct `AuditTypeDefinition` class from the registry.
    *   Call the `calculate_score(response)` method from that class.
    *   Save the returned score to the `AuditResponse.score` field.
3.  **Add Tests**: Create tests for each `AuditTypeDefinition` to ensure their `calculate_score` methods work correctly with sample `AuditResponse` data.

**Primary Files**:
*   `backend/app/audit_types/*`
*   `backend/app/api/routes/audit_assignments.py`
*   `backend/app/api/routes/audit_responses.py`
*   `backend/app/crud.py`
*   Associated test files.

---

## Future Development (Once Deployed)

### Task 5: Develop Data Analytics and KPI Dashboard

**Description**:
To provide actionable insights from the collected audit data, a dedicated analytics module is required. This will involve creating new API endpoints to compute, aggregate, and serve historical data, trends, and Key Performance Indicators (KPIs). This feature will be developed in phases to manage complexity and ensure application performance.

**Action Plan**:

**Phase 1: Foundational KPI Endpoints**
1.  **Define Initial KPIs**: Start with a core set of metrics, such as:
    *   Average audit score over time (per template, per company, per area).
    *   Audit completion rate (assigned vs. submitted).
    *   Frequency of non-compliant answers (e.g., count of "No" answers in a security checklist).
    *   Trends in scores for recurring audits.
2.  **Create Analytics Endpoints**: Develop a new set of non-RESTful endpoints under `/api/v1/analytics/`.
    *   Example: `GET /api/v1/analytics/score-trends?template_id=...&time_period=monthly`
3.  **Implement Optimized Queries**: Create new functions in a dedicated `backend/app/crud_analytics.py` file. These functions will contain optimized SQL queries (`GROUP BY`, `AVG`, `COUNT`, date truncations) to compute the KPIs directly from the production database. These queries must be carefully written to be efficient.
4.  **New Pydantic Models**: Create schemas in `models.py` to define the structure of the data returned by the analytics endpoints.

**Phase 2: Long-Term Scalability - ETL and Data Mart**
1.  **Problem Statement**: As the volume of audit data grows, running complex analytical queries directly on the main transactional database will degrade application performance and is not scalable.
2.  **ETL Process**: Develop an ETL (Extract, Transform, Load) process. This will be a background script/service that runs periodically (e.g., nightly).
    *   **Extract**: Reads new `AuditResponse` and `Answer` data from the production database.
    *   **Transform**: Aggregates the data into a pre-calculated, analysis-friendly format (e.g., a daily summary table).
    *   **Load**: Inserts the transformed data into a separate, read-optimized database (a "data mart" or "data warehouse").
3.  **Refactor Analytics Endpoints**: Modify the `/api/v1/analytics/` endpoints to query the fast, responsive data mart instead of the live production database.
4.  **Benefits**: This approach isolates the analytical workload, ensures the main application remains fast, and allows for much more complex and historical analysis without performance penalties.

**Primary Files & Components**:
*   `backend/app/api/routes/analytics.py` (new file)
*   `backend/app/crud_analytics.py` (new file)
*   `backend/app/models.py` (for new response schemas)
*   A new ETL script/service (for Phase 2)
*   Infrastructure for a separate analytics database (for Phase 2)

---