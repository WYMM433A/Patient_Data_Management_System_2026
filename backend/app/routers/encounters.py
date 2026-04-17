from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import require_permission
from app.schemas.encounters import (
    EncounterCreate, EncounterOut,
    SOAPNoteUpdate, SOAPNoteOut,
    VitalsCreate, VitalsOut,
    DiagnosisCreate, DiagnosisOut,
)
from app.services import encounter_service

router = APIRouter(prefix="/encounters", tags=["Encounters"])


# ---------------------------------------------------------------------------
# Encounter CRUD
# ---------------------------------------------------------------------------

@router.post("", response_model=EncounterOut, status_code=status.HTTP_201_CREATED)
def create_encounter(
    payload: EncounterCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("create_encounter")),
):
    return encounter_service.create_encounter(db, payload, current_user.user_id)


@router.get("", response_model=List[EncounterOut])
def list_encounters(
    patient_id: Optional[UUID] = None,
    doctor_id:  Optional[UUID] = None,
    enc_status: Optional[str]  = None,
    skip:  int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_permission("create_encounter")),
):
    return encounter_service.list_encounters(db, patient_id, doctor_id, enc_status, skip, limit)


@router.get("/{encounter_id}", response_model=EncounterOut)
def get_encounter(
    encounter_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("create_encounter")),
):
    return encounter_service.get_encounter(db, encounter_id)


@router.post("/{encounter_id}/close", response_model=EncounterOut)
def close_encounter(
    encounter_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("create_encounter")),
):
    return encounter_service.close_encounter(db, encounter_id)


# ---------------------------------------------------------------------------
# SOAP Notes  (one per encounter, shell created atomically by stored proc)
# ---------------------------------------------------------------------------

@router.get("/{encounter_id}/soap", response_model=SOAPNoteOut)
def get_soap_note(
    encounter_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("create_encounter")),
):
    return encounter_service.get_soap_note(db, encounter_id)


@router.patch("/{encounter_id}/soap", response_model=SOAPNoteOut)
def update_soap_note(
    encounter_id: UUID,
    payload: SOAPNoteUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("create_encounter")),
):
    return encounter_service.update_soap_note(db, encounter_id, payload)


# ---------------------------------------------------------------------------
# Vitals
# ---------------------------------------------------------------------------

@router.post("/{encounter_id}/vitals", response_model=VitalsOut, status_code=status.HTTP_201_CREATED)
def add_vitals(
    encounter_id: UUID,
    payload: VitalsCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("create_encounter")),
):
    return encounter_service.add_vitals(db, encounter_id, payload, current_user.user_id)


@router.get("/{encounter_id}/vitals", response_model=List[VitalsOut])
def list_vitals(
    encounter_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("create_encounter")),
):
    return encounter_service.list_vitals(db, encounter_id)


# ---------------------------------------------------------------------------
# Diagnoses
# ---------------------------------------------------------------------------

@router.post("/{encounter_id}/diagnoses", response_model=DiagnosisOut, status_code=status.HTTP_201_CREATED)
def add_diagnosis(
    encounter_id: UUID,
    payload: DiagnosisCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("create_encounter")),
):
    return encounter_service.add_diagnosis(db, encounter_id, payload, current_user.user_id)


@router.get("/{encounter_id}/diagnoses", response_model=List[DiagnosisOut])
def list_diagnoses(
    encounter_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("create_encounter")),
):
    return encounter_service.list_diagnoses(db, encounter_id)


@router.delete("/{encounter_id}/diagnoses/{diagnosis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diagnosis(
    encounter_id: UUID,
    diagnosis_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("create_encounter")),
):
    encounter_service.delete_diagnosis(db, encounter_id, diagnosis_id)
