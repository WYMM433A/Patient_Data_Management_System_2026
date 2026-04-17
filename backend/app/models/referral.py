import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship

from app.database import Base


class Referral(Base):
    __tablename__ = "referrals"
    # Audit trigger on this table — disable OUTPUT clause
    __table_args__ = {"implicit_returning": False}

    referral_id  = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UNIQUEIDENTIFIER, ForeignKey("encounters.encounter_id"), nullable=False)
    patient_id   = Column(UNIQUEIDENTIFIER, ForeignKey("patients.patient_id"),     nullable=False)
    referred_by  = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"),           nullable=False)
    specialty    = Column(String(100), nullable=False)
    reason       = Column(String,      nullable=True)
    urgency      = Column(String(20),  nullable=False, default="routine")
    status       = Column(String(20),  nullable=False, default="pending")
    referred_at  = Column(DateTime,    nullable=False, server_default="GETDATE()")
    event_date   = Column(DateTime,    nullable=True)

    encounter = relationship("Encounter", foreign_keys=[encounter_id])
    patient   = relationship("Patient",   foreign_keys=[patient_id])
    referrer  = relationship("User",      foreign_keys=[referred_by])
