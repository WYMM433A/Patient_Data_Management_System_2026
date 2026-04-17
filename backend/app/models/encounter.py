import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Numeric, Date
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship

from app.database import Base


class Encounter(Base):
    __tablename__ = "encounters"
    # Audit trigger on this table — disable OUTPUT clause
    __table_args__ = {"implicit_returning": False}

    encounter_id    = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    patient_id      = Column(UNIQUEIDENTIFIER, ForeignKey("patients.patient_id"),      nullable=False)
    doctor_id       = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"),             nullable=False)
    appointment_id  = Column(UNIQUEIDENTIFIER, ForeignKey("appointments.appointment_id"), nullable=True)
    encounter_date  = Column(DateTime,  nullable=False, server_default="GETDATE()")
    encounter_type  = Column(String(20), nullable=False)
    chief_complaint = Column(String,     nullable=True)
    status          = Column(String(10), nullable=False, default="open")
    visit_number    = Column(Integer,    nullable=False, default=1)
    created_at      = Column(DateTime,  nullable=False, server_default="GETDATE()")
    closed_at       = Column(DateTime,  nullable=True)

    patient        = relationship("Patient",     foreign_keys=[patient_id])
    doctor         = relationship("User",        foreign_keys=[doctor_id])
    clinical_notes = relationship("ClinicalNote", back_populates="encounter")
    vitals         = relationship("Vital",        back_populates="encounter")
    diagnoses      = relationship("Diagnosis",    back_populates="encounter")


class ClinicalNote(Base):
    __tablename__ = "clinical_notes"
    # Audit trigger on this table — disable OUTPUT clause
    __table_args__ = {"implicit_returning": False}

    note_id      = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UNIQUEIDENTIFIER, ForeignKey("encounters.encounter_id"), nullable=False)
    doctor_id    = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"),           nullable=False)
    subjective   = Column(String,  nullable=True)
    objective    = Column(String,  nullable=True)
    assessment   = Column(String,  nullable=True)
    # [plan] is a reserved word in SQL Server — map explicitly
    plan         = Column("plan", String, nullable=True)
    recorded_at  = Column(DateTime, nullable=False, server_default="GETDATE()")
    event_date   = Column(DateTime, nullable=True)
    validated_at = Column(DateTime, nullable=True)
    updated_at   = Column(DateTime, nullable=True)

    encounter = relationship("Encounter", back_populates="clinical_notes")


class Diagnosis(Base):
    __tablename__ = "diagnoses"
    # Audit trigger on this table — disable OUTPUT clause
    __table_args__ = {"implicit_returning": False}

    diagnosis_id   = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    encounter_id   = Column(UNIQUEIDENTIFIER, ForeignKey("encounters.encounter_id"),  nullable=False)
    patient_id     = Column(UNIQUEIDENTIFIER, ForeignKey("patients.patient_id"),      nullable=False)
    icd_code       = Column(String(10), nullable=False)
    description    = Column(String,      nullable=True)
    diagnosis_type = Column(String(20),  nullable=False)
    condition      = Column(String(20),  nullable=True)
    timing         = Column(String(20),  nullable=True)
    is_chronic     = Column(Boolean,     nullable=False, default=False)
    diagnosed_by   = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"), nullable=False)
    recorded_at    = Column(DateTime, nullable=False, server_default="GETDATE()")
    event_date     = Column(Date,     nullable=True)
    validated_at   = Column(DateTime, nullable=True)

    encounter = relationship("Encounter", back_populates="diagnoses")


class Vital(Base):
    __tablename__ = "vitals"
    # Audit trigger on this table — disable OUTPUT clause
    __table_args__ = {"implicit_returning": False}

    vital_id           = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    patient_id         = Column(UNIQUEIDENTIFIER, ForeignKey("patients.patient_id"),      nullable=False)
    encounter_id       = Column(UNIQUEIDENTIFIER, ForeignKey("encounters.encounter_id"),  nullable=False)
    recorded_by        = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"),             nullable=False)
    blood_pressure_sys = Column(Integer,        nullable=True)
    blood_pressure_dia = Column(Integer,        nullable=True)
    heart_rate         = Column(Integer,        nullable=True)
    temperature        = Column(Numeric(4, 1),  nullable=True)
    weight_kg          = Column(Numeric(5, 2),  nullable=True)
    height_cm          = Column(Numeric(5, 2),  nullable=True)
    oxygen_saturation  = Column(Integer,        nullable=True)
    respiratory_rate   = Column(Integer,        nullable=True)
    bmi                = Column(Numeric(4, 2),  nullable=True)   # auto-calculated by trigger
    is_abnormal        = Column(Boolean,        nullable=False, default=False)  # auto-set by trigger
    recorded_at        = Column(DateTime, nullable=False, server_default="GETDATE()")
    event_date         = Column(DateTime, nullable=True)
    validated_at       = Column(DateTime, nullable=True)

    encounter = relationship("Encounter", back_populates="vitals")
