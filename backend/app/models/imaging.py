import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship

from app.database import Base


class ImagingRecord(Base):
    __tablename__ = "imaging_records"
    # Audit trigger on this table — disable OUTPUT clause
    __table_args__ = {"implicit_returning": False}

    imaging_id        = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    patient_id        = Column(UNIQUEIDENTIFIER, ForeignKey("patients.patient_id"),    nullable=False)
    encounter_id      = Column(UNIQUEIDENTIFIER, ForeignKey("encounters.encounter_id"), nullable=False)
    ordered_by        = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"),           nullable=False)
    imaging_type      = Column(String(50),  nullable=True)
    body_part         = Column(String(100), nullable=True)
    findings          = Column(String,      nullable=True)
    image_url         = Column(String(500), nullable=True)
    radiologist_notes = Column(String,      nullable=True)
    performed_at      = Column(DateTime,    nullable=False, server_default="GETDATE()")
    event_date        = Column(DateTime,    nullable=True)
    validated_at      = Column(DateTime,    nullable=True)

    encounter = relationship("Encounter", foreign_keys=[encounter_id])
    patient   = relationship("Patient",   foreign_keys=[patient_id])
    orderer   = relationship("User",      foreign_keys=[ordered_by])
