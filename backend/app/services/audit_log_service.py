from uuid import UUID
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def list_audit_logs(
    db: Session,
    user_id:        Optional[UUID] = None,
    action:         Optional[str]  = None,
    table_affected: Optional[str]  = None,
    record_id:      Optional[UUID] = None,
    date_from:      Optional[datetime] = None,
    date_to:        Optional[datetime] = None,
    skip:  int = 0,
    limit: int = 100,
) -> List[AuditLog]:
    q = db.query(AuditLog)

    if user_id:
        q = q.filter(AuditLog.user_id == str(user_id))
    if action:
        q = q.filter(AuditLog.action == action.upper())
    if table_affected:
        q = q.filter(AuditLog.table_affected == table_affected)
    if record_id:
        q = q.filter(AuditLog.record_id == str(record_id))
    if date_from:
        q = q.filter(AuditLog.timestamp >= date_from)
    if date_to:
        q = q.filter(AuditLog.timestamp <= date_to)

    return q.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
