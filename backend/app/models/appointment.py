import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship

from app.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    appointment_id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    patient_id     = Column(UNIQUEIDENTIFIER, ForeignKey("patients.patient_id"), nullable=False)
    doctor_id      = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"),       nullable=False)
    scheduled_at   = Column(DateTime,         nullable=False)
    reason         = Column(String,           nullable=True)
    status         = Column(String(20),       nullable=False, default="scheduled")
    notes          = Column(String,           nullable=True)
    checked_at     = Column(DateTime,         nullable=True)
    created_by     = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"),       nullable=False)
    created_at     = Column(DateTime,         nullable=False, server_default=func.getdate())

    patient = relationship("Patient", foreign_keys=[patient_id])
    doctor  = relationship("User",    foreign_keys=[doctor_id])
    creator = relationship("User",    foreign_keys=[created_by])
