import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id         = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    user_id        = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"), nullable=True)
    action         = Column(String(20),  nullable=False)
    module         = Column(String(50),  nullable=True)
    table_affected = Column(String(100), nullable=True)
    record_id      = Column(UNIQUEIDENTIFIER, nullable=True)
    old_value      = Column(String,      nullable=True)
    new_value      = Column(String,      nullable=True)
    ip_address     = Column(String(45),  nullable=True)
    user_agent     = Column(String(500), nullable=True)
    timestamp      = Column(DateTime,    nullable=False, server_default="GETDATE()")
