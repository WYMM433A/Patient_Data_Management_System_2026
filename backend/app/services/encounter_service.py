from uuid import UUID
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException, status


from app.models.encounter import Encounter, ClinicalNote, Diagnosis, Vital
from app.schemas.encounters import (
    EncounterCreate,
    SOAPNoteUpdate,
    VitalsCreate,
    DiagnosisCreate,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_encounter_or_404(db: Session, encounter_id: UUID) -> Encounter:
    enc = db.query(Encounter).filter(
        Encounter.encounter_id == str(encounter_id)
    ).first()
    if not enc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")
    return enc


def _assert_open(enc: Encounter) -> None:
    if enc.status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Encounter is already closed",
        )


# ---------------------------------------------------------------------------
# Encounter CRUD
# ---------------------------------------------------------------------------

def create_encounter(db: Session, payload: EncounterCreate, created_by: UUID) -> Encounter:
    """
    Delegates to usp_create_encounter (ACID stored procedure).
    The proc atomically:
      - inserts the encounter row
      - increments visit_number
      - marks the linked appointment as 'completed'
      - inserts an empty SOAP note shell
      - writes an audit log entry
    """
    sql = text("""
        DECLARE @new_id UNIQUEIDENTIFIER;
        EXEC usp_create_encounter
            @p_patient_id      = :patient_id,
            @p_doctor_id       = :doctor_id,
            @p_appointment_id  = :appointment_id,
            @p_encounter_type  = :enc_type,
            @p_chief_complaint = :complaint,
            @p_created_by      = :created_by,
            @p_encounter_id    = @new_id OUTPUT;
        SELECT @new_id AS encounter_id;
    """)

    result = db.execute(sql, {
        "patient_id":     str(payload.patient_id),
        "doctor_id":      str(payload.doctor_id),
        "appointment_id": str(payload.appointment_id) if payload.appointment_id else None,
        "enc_type":       payload.encounter_type,
        "complaint":      payload.chief_complaint,
        "created_by":     str(created_by),
    })
    new_id = result.scalar()
    db.commit()

    if not new_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored procedure did not return encounter_id",
        )

    enc = db.query(Encounter).filter(
        Encounter.encounter_id == str(new_id)
    ).first()
    if not enc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Encounter created but could not be fetched",
        )
    return enc


def list_encounters(
    db: Session,
    patient_id:  Optional[UUID] = None,
    doctor_id:   Optional[UUID] = None,
    enc_status:  Optional[str]  = None,
    skip:  int = 0,
    limit: int = 50,
) -> List[Encounter]:
    q = db.query(Encounter)
    if patient_id:
        q = q.filter(Encounter.patient_id == str(patient_id))
    if doctor_id:
        q = q.filter(Encounter.doctor_id == str(doctor_id))
    if enc_status:
        q = q.filter(Encounter.status == enc_status)
    return q.order_by(Encounter.encounter_date.desc()).offset(skip).limit(limit).all()


def get_encounter(db: Session, encounter_id: UUID) -> Encounter:
    return _get_encounter_or_404(db, encounter_id)


def close_encounter(db: Session, encounter_id: UUID) -> Encounter:
    enc = _get_encounter_or_404(db, encounter_id)
    _assert_open(enc)
    enc.status    = "closed"
    enc.closed_at = datetime.utcnow()
    db.commit()
    db.refresh(enc)
    return enc


# ---------------------------------------------------------------------------
# SOAP Notes  (one note per encounter; shell created by stored proc)
# ---------------------------------------------------------------------------

def get_soap_note(db: Session, encounter_id: UUID) -> ClinicalNote:
    _get_encounter_or_404(db, encounter_id)
    note = db.query(ClinicalNote).filter(
        ClinicalNote.encounter_id == str(encounter_id)
    ).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOAP note not found")
    return note


def update_soap_note(
    db: Session, encounter_id: UUID, payload: SOAPNoteUpdate
) -> ClinicalNote:
    enc = _get_encounter_or_404(db, encounter_id)
    _assert_open(enc)

    note = db.query(ClinicalNote).filter(
        ClinicalNote.encounter_id == str(encounter_id)
    ).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOAP note not found")

    for field, val in payload.model_dump(exclude_none=True).items():
        setattr(note, field, val)
    note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    return note


# ---------------------------------------------------------------------------
# Vitals
# ---------------------------------------------------------------------------

def add_vitals(
    db: Session,
    encounter_id: UUID,
    payload: VitalsCreate,
    recorded_by: UUID,
) -> Vital:
    enc = _get_encounter_or_404(db, encounter_id)
    _assert_open(enc)

    vital = Vital(
        patient_id         = str(enc.patient_id),
        encounter_id       = str(encounter_id),
        recorded_by        = str(recorded_by),
        blood_pressure_sys = payload.blood_pressure_sys,
        blood_pressure_dia = payload.blood_pressure_dia,
        heart_rate         = payload.heart_rate,
        temperature        = payload.temperature,
        weight_kg          = payload.weight_kg,
        height_cm          = payload.height_cm,
        oxygen_saturation  = payload.oxygen_saturation,
        respiratory_rate   = payload.respiratory_rate,
        event_date         = payload.event_date,
    )
    db.add(vital)
    db.commit()
    db.refresh(vital)
    return vital


def list_vitals(db: Session, encounter_id: UUID) -> List[Vital]:
    _get_encounter_or_404(db, encounter_id)
    return (
        db.query(Vital)
        .filter(Vital.encounter_id == str(encounter_id))
        .order_by(Vital.recorded_at.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Diagnoses
# ---------------------------------------------------------------------------

def add_diagnosis(
    db: Session,
    encounter_id: UUID,
    payload: DiagnosisCreate,
    diagnosed_by: UUID,
) -> Diagnosis:
    enc = _get_encounter_or_404(db, encounter_id)
    _assert_open(enc)

    diag = Diagnosis(
        encounter_id   = str(encounter_id),
        patient_id     = str(enc.patient_id),
        icd_code       = payload.icd_code,
        description    = payload.description,
        diagnosis_type = payload.diagnosis_type,
        condition      = payload.condition,
        timing         = payload.timing,
        is_chronic     = payload.is_chronic,
        diagnosed_by   = str(diagnosed_by),
        event_date     = payload.event_date,
    )
    db.add(diag)
    db.commit()
    db.refresh(diag)
    return diag


def list_diagnoses(db: Session, encounter_id: UUID) -> List[Diagnosis]:
    _get_encounter_or_404(db, encounter_id)
    return (
        db.query(Diagnosis)
        .filter(Diagnosis.encounter_id == str(encounter_id))
        .order_by(Diagnosis.recorded_at)
        .all()
    )


def delete_diagnosis(db: Session, encounter_id: UUID, diagnosis_id: UUID) -> None:
    enc = _get_encounter_or_404(db, encounter_id)
    _assert_open(enc)
    diag = (
        db.query(Diagnosis)
        .filter(
            Diagnosis.diagnosis_id == str(diagnosis_id),
            Diagnosis.encounter_id == str(encounter_id),
        )
        .first()
    )
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    db.delete(diag)
    db.commit()
