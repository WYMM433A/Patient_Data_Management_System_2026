from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user, require_permission
from app.schemas.patients import (
    PatientCreate, PatientUpdate, PatientOut,
    MedicalHistoryCreate, MedicalHistoryOut,
    AllergyCreate, AllergyOut,
    VaccinationCreate, VaccinationOut,
)
from app.services import patient_service

router = APIRouter(prefix="/patients", tags=["Patients"])


# ---------- Patients ----------

@router.get("", response_model=List[PatientOut])
def list_patients(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_permission("view_patient_record")),
):
    return patient_service.list_patients(db, search, skip, limit)


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("create_patient")),
):
    return patient_service.create_patient(db, payload, current_user.user_id)


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("view_patient_record")),
):
    return patient_service.get_patient(db, patient_id)


@router.patch("/{patient_id}", response_model=PatientOut)
def update_patient(
    patient_id: UUID,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("create_patient")),
):
    return patient_service.update_patient(db, patient_id, payload)


# ---------- Medical History ----------

@router.get("/{patient_id}/medical-history", response_model=List[MedicalHistoryOut])
def list_medical_history(
    patient_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("view_medical_history")),
):
    return patient_service.list_medical_history(db, patient_id)


@router.post("/{patient_id}/medical-history", response_model=MedicalHistoryOut, status_code=status.HTTP_201_CREATED)
def add_medical_history(
    patient_id: UUID,
    payload: MedicalHistoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("manage_medical_history")),
):
    return patient_service.add_medical_history(db, patient_id, payload, current_user.user_id)


@router.delete("/{patient_id}/medical-history/{history_id}", response_model=MedicalHistoryOut)
def remove_medical_history(
    patient_id: UUID,
    history_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("manage_medical_history")),
):
    return patient_service.remove_medical_history(db, patient_id, history_id)


# ---------- Allergies ----------

@router.get("/{patient_id}/allergies", response_model=List[AllergyOut])
def list_allergies(
    patient_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("view_medical_history")),
):
    return patient_service.list_allergies(db, patient_id)


@router.post("/{patient_id}/allergies", response_model=AllergyOut, status_code=status.HTTP_201_CREATED)
def add_allergy(
    patient_id: UUID,
    payload: AllergyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("manage_medical_history")),
):
    return patient_service.add_allergy(db, patient_id, payload, current_user.user_id)


@router.delete("/{patient_id}/allergies/{allergy_id}", response_model=AllergyOut)
def remove_allergy(
    patient_id: UUID,
    allergy_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("manage_medical_history")),
):
    return patient_service.remove_allergy(db, patient_id, allergy_id)


# ---------- Vaccinations ----------

@router.get("/{patient_id}/vaccinations", response_model=List[VaccinationOut])
def list_vaccinations(
    patient_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("view_patient_record")),
):
    return patient_service.list_vaccinations(db, patient_id)


@router.post("/{patient_id}/vaccinations", response_model=VaccinationOut, status_code=status.HTTP_201_CREATED)
def add_vaccination(
    patient_id: UUID,
    payload: VaccinationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("update_vaccinations")),
):
    return patient_service.add_vaccination(db, patient_id, payload, current_user.user_id)
