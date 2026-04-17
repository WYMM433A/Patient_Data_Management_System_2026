import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship

from app.database import Base


class Prescription(Base):
    __tablename__ = "prescriptions"
    # Audit trigger on this table — disable OUTPUT clause
    __table_args__ = {"implicit_returning": False}

    prescription_id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    encounter_id    = Column(UNIQUEIDENTIFIER, ForeignKey("encounters.encounter_id"), nullable=False)
    patient_id      = Column(UNIQUEIDENTIFIER, ForeignKey("patients.patient_id"),     nullable=False)
    doctor_id       = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"),           nullable=False)
    drug_name       = Column(String(200), nullable=False)
    dosage          = Column(String(50),  nullable=True)
    frequency       = Column(String(50),  nullable=True)
    duration        = Column(String(50),  nullable=True)
    route           = Column(String(30),  nullable=True)
    instructions    = Column(String,      nullable=True)
    is_active       = Column(Boolean,     nullable=False, default=True)
    is_removed      = Column(Boolean,     nullable=False, default=False)
    issued_at       = Column(DateTime,    nullable=False, server_default="GETDATE()")
    event_date      = Column(DateTime,    nullable=True)
    validated_at    = Column(DateTime,    nullable=True)

    encounter = relationship("Encounter", foreign_keys=[encounter_id])
    patient   = relationship("Patient",   foreign_keys=[patient_id])
    doctor    = relationship("User",      foreign_keys=[doctor_id])
