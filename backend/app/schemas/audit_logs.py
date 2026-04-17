from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime


class AuditLogOut(BaseModel):
    log_id:         UUID
    user_id:        Optional[UUID]
    action:         str
    module:         Optional[str]
    table_affected: Optional[str]
    record_id:      Optional[UUID]
    old_value:      Optional[str]
    new_value:      Optional[str]
    ip_address:     Optional[str]
    user_agent:     Optional[str]
    timestamp:      datetime

    model_config = {"from_attributes": True}
