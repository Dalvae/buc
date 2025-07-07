from fastapi import APIRouter

# Direct imports of router objects from their respective modules
from app.api.routes.login import router as login_router
from app.api.routes.private import router as private_router
from app.api.routes.users import router as users_router
from app.api.routes.utils import router as utils_router
from app.api.routes.companies import router as companies_router
from app.api.routes.areas import router as areas_router
from app.api.routes.audit_templates import router as audit_templates_router
from app.api.routes.audit_assignments import router as audit_assignments_router
from app.api.routes.audit_responses import router as audit_responses_router
from app.api.routes.assigned_questions import router as assigned_questions_router

from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login_router)
api_router.include_router(users_router)
api_router.include_router(utils_router)
api_router.include_router(companies_router)
api_router.include_router(areas_router)
api_router.include_router(audit_templates_router)
api_router.include_router(audit_assignments_router)
api_router.include_router(audit_responses_router)
api_router.include_router(assigned_questions_router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private_router)
