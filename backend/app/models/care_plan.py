import uuid
from sqlalchemy import Column, String, DateTime, Date, ForeignKey
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship

from app.database import Base


class CarePlan(Base):
    __tablename__ = "care_plans"
    # Audit trigger on this table — disable OUTPUT clause
    __table_args__ = {"implicit_returning": False}

    plan_id       = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    patient_id    = Column(UNIQUEIDENTIFIER, ForeignKey("patients.patient_id"), nullable=False)
    doctor_id     = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"),       nullable=False)
    condition     = Column(String(200), nullable=False)
    goals         = Column(String,      nullable=True)
    interventions = Column(String,      nullable=True)
    start_date    = Column(Date,        nullable=False)
    review_date   = Column(Date,        nullable=True)
    status        = Column(String(20),  nullable=False, default="active")
    notes         = Column(String,      nullable=True)
    created_at    = Column(DateTime,    nullable=False, server_default="GETDATE()")
    updated_at    = Column(DateTime,    nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])
    doctor  = relationship("User",    foreign_keys=[doctor_id])
