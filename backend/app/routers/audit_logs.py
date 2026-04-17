from uuid import UUID
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import require_permission
from app.schemas.audit_logs import AuditLogOut
from app.services import audit_log_service

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogOut])
def list_audit_logs(
    user_id:        Optional[UUID] = None,
    action:         Optional[str]  = None,
    table_affected: Optional[str]  = None,
    record_id:      Optional[UUID] = None,
    date_from:      Optional[datetime] = None,
    date_to:        Optional[datetime] = None,
    skip:  int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _=Depends(require_permission("view_audit_logs")),
):
    return audit_log_service.list_audit_logs(
        db,
        user_id=user_id,
        action=action,
        table_affected=table_affected,
        record_id=record_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
