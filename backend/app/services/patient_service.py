from uuid import UUID
from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from fastapi import HTTPException, status

from app.models.patient import Patient, MedicalHistory, Allergy, Vaccination
from app.schemas.patients import (
    PatientCreate, PatientUpdate,
    MedicalHistoryCreate, AllergyCreate, VaccinationCreate,
)


# -------------------------------------------------------------------
# MRN generation: PDMS-YYYY-NNNNN
# -------------------------------------------------------------------

def _generate_mrn(db: Session) -> str:
    year = date.today().year
    prefix = f"PDMS-{year}-"
    # Find highest sequence for this year
    last = (
        db.query(Patient)
        .filter(Patient.mrn.like(f"{prefix}%"))
        .order_by(Patient.mrn.desc())
        .first()
    )
    if last:
        seq = int(last.mrn.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:05d}"


# -------------------------------------------------------------------
# Patient CRUD
# -------------------------------------------------------------------

def _get_patient_or_404(db: Session, patient_id: UUID) -> Patient:
    p = db.query(Patient).filter(Patient.patient_id == str(patient_id)).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return p


def list_patients(
    db: Session,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Patient]:
    q = db.query(Patient)
    if search:
        term = f"%{search}%"
        q = q.filter(
            or_(
                Patient.first_name.ilike(term),
                Patient.last_name.ilike(term),
                Patient.mrn.ilike(term),
                Patient.phone.ilike(term),
            )
        )
    return q.order_by(Patient.last_name, Patient.first_name).offset(skip).limit(limit).all()


def get_patient(db: Session, patient_id: UUID) -> Patient:
    return _get_patient_or_404(db, patient_id)


def create_patient(db: Session, payload: PatientCreate, created_by_id: UUID) -> Patient:
    mrn = _generate_mrn(db)
    patient = Patient(
        mrn=mrn,
        first_name=payload.first_name,
        last_name=payload.last_name,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        blood_type=payload.blood_type,
        phone=payload.phone,
        email=payload.email,
        address=payload.address,
        emergency_contact_name=payload.emergency_contact_name,
        emergency_contact_phone=payload.emergency_contact_phone,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def update_patient(db: Session, patient_id: UUID, payload: PatientUpdate) -> Patient:
    patient = _get_patient_or_404(db, patient_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient


# -------------------------------------------------------------------
# Medical History
# -------------------------------------------------------------------

def add_medical_history(db: Session, patient_id: UUID, payload: MedicalHistoryCreate, recorded_by: UUID) -> MedicalHistory:
    _get_patient_or_404(db, patient_id)
    entry = MedicalHistory(
        patient_id=str(patient_id),
        condition_name=payload.condition_name,
        icd_code=payload.icd_code,
        onset_date=payload.onset_date,
        is_chronic=payload.is_chronic,
        notes=payload.notes,
        recorded_by=str(recorded_by),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_medical_history(db: Session, patient_id: UUID) -> List[MedicalHistory]:
    _get_patient_or_404(db, patient_id)
    return (
        db.query(MedicalHistory)
        .filter(MedicalHistory.patient_id == str(patient_id), MedicalHistory.is_removed == False)
        .all()
    )


def remove_medical_history(db: Session, patient_id: UUID, history_id: UUID) -> MedicalHistory:
    entry = db.query(MedicalHistory).filter(
        MedicalHistory.history_id == str(history_id),
        MedicalHistory.patient_id == str(patient_id),
    ).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical history entry not found")
    entry.is_removed = True
    db.commit()
    db.refresh(entry)
    return entry


# -------------------------------------------------------------------
# Allergies
# -------------------------------------------------------------------

def add_allergy(db: Session, patient_id: UUID, payload: AllergyCreate, recorded_by: UUID) -> Allergy:
    _get_patient_or_404(db, patient_id)
    allergy = Allergy(
        patient_id=str(patient_id),
        allergen=payload.allergen,
        reaction_type=payload.reaction_type,
        severity=payload.severity,
        recorded_by=str(recorded_by),
    )
    db.add(allergy)
    db.commit()
    db.refresh(allergy)
    return allergy


def list_allergies(db: Session, patient_id: UUID) -> List[Allergy]:
    _get_patient_or_404(db, patient_id)
    return (
        db.query(Allergy)
        .filter(Allergy.patient_id == str(patient_id), Allergy.is_removed == False)
        .all()
    )


def remove_allergy(db: Session, patient_id: UUID, allergy_id: UUID) -> Allergy:
    allergy = db.query(Allergy).filter(
        Allergy.allergy_id == str(allergy_id),
        Allergy.patient_id == str(patient_id),
    ).first()
    if not allergy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allergy not found")
    allergy.is_removed = True
    db.commit()
    db.refresh(allergy)
    return allergy


# -------------------------------------------------------------------
# Vaccinations
# -------------------------------------------------------------------

def add_vaccination(db: Session, patient_id: UUID, payload: VaccinationCreate, administered_by: UUID) -> Vaccination:
    _get_patient_or_404(db, patient_id)
    vacc = Vaccination(
        patient_id=str(patient_id),
        vaccine_name=payload.vaccine_name,
        dose_number=payload.dose_number,
        administered_by=str(administered_by),
        administered_at=payload.administered_at,
        next_due_date=payload.next_due_date,
        notes=payload.notes,
    )
    db.add(vacc)
    db.commit()
    db.refresh(vacc)
    return vacc


def list_vaccinations(db: Session, patient_id: UUID) -> List[Vaccination]:
    _get_patient_or_404(db, patient_id)
    return (
        db.query(Vaccination)
        .filter(Vaccination.patient_id == str(patient_id))
        .order_by(Vaccination.administered_at.desc())
        .all()
    )
