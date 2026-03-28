import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Date, Integer, ForeignKey, func
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship

from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    patient_id              = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    mrn                     = Column(String(20), nullable=False, unique=True)
    first_name              = Column(String(100), nullable=False)
    last_name               = Column(String(100), nullable=False)
    date_of_birth           = Column(Date, nullable=False)
    gender                  = Column(String(20), nullable=True)
    blood_type              = Column(String(5), nullable=True)
    phone                   = Column(String(20), nullable=True)
    email                   = Column(String(150), nullable=True)
    address                 = Column(String, nullable=True)
    emergency_contact_name  = Column(String(150), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    created_at              = Column(DateTime, nullable=False, server_default=func.getdate())

    medical_history = relationship("MedicalHistory", back_populates="patient")
    allergies       = relationship("Allergy",        back_populates="patient")
    vaccinations    = relationship("Vaccination",    back_populates="patient")


class MedicalHistory(Base):
    __tablename__ = "medical_history"
    __table_args__ = {"implicit_returning": False}  # table has audit trigger — OUTPUT clause not allowed

    history_id      = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    patient_id      = Column(UNIQUEIDENTIFIER, ForeignKey("patients.patient_id"), nullable=False)
    condition_name  = Column(String(200), nullable=False)
    icd_code        = Column(String(10), nullable=True)
    onset_date      = Column(Date, nullable=True)
    resolution_date = Column(Date, nullable=True)
    is_chronic      = Column(Boolean, nullable=False, default=False)
    is_removed      = Column(Boolean, nullable=False, default=False)
    notes           = Column(String, nullable=True)
    recorded_by     = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"), nullable=True)
    recorded_at     = Column(DateTime, nullable=False, server_default=func.getdate())

    patient = relationship("Patient", back_populates="medical_history")


class Allergy(Base):
    __tablename__ = "allergies"
    __table_args__ = {"implicit_returning": False}  # table has audit trigger — OUTPUT clause not allowed

    allergy_id    = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    patient_id    = Column(UNIQUEIDENTIFIER, ForeignKey("patients.patient_id"), nullable=False)
    allergen      = Column(String(200), nullable=False)
    reaction_type = Column(String(100), nullable=True)
    severity      = Column(String(20), nullable=True)
    is_removed    = Column(Boolean, nullable=False, default=False)
    recorded_by   = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"), nullable=True)
    recorded_at   = Column(DateTime, nullable=False, server_default=func.getdate())

    patient = relationship("Patient", back_populates="allergies")


class Vaccination(Base):
    __tablename__ = "vaccinations"
    __table_args__ = {"implicit_returning": False}  # table has audit trigger — OUTPUT clause not allowed

    vaccination_id  = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    patient_id      = Column(UNIQUEIDENTIFIER, ForeignKey("patients.patient_id"), nullable=False)
    vaccine_name    = Column(String(200), nullable=False)
    dose_number     = Column(Integer, nullable=True)
    administered_by = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"), nullable=True)
    administered_at = Column(Date, nullable=False)
    next_due_date   = Column(Date, nullable=True)
    notes           = Column(String, nullable=True)
    recorded_at     = Column(DateTime, nullable=False, server_default=func.getdate())

    patient = relationship("Patient", back_populates="vaccinations")
