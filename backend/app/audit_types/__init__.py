from typing import Any

from app.audit_types.base import AuditTypeDefinitionBase
from app.audit_types.five_s_audit import FiveSAuditType
from app.audit_types.security_checklist_audit import SecurityChecklistAuditType


AUDIT_TYPE_DEFINITIONS: dict[str, type[AuditTypeDefinitionBase]] = {
    FiveSAuditType().get_key(): FiveSAuditType,
    SecurityChecklistAuditType().get_key(): SecurityChecklistAuditType,
}

def get_audit_type_definition(key: str) -> AuditTypeDefinitionBase | None:
    """Retrieves an AuditTypeDefinition instance by its unique key."""
    audit_type_class = AUDIT_TYPE_DEFINITIONS.get(key)
    if audit_type_class:
        return audit_type_class()
    return None