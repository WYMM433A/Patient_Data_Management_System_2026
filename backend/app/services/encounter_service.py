from uuid import UUID
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException, status


from app.models.encounter import Encounter, ClinicalNote, Diagnosis, Vital
from app.models.appointment import Appointment
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
    Validates that the appointment exists, belongs to the same patient,
    and is in 'checked_in' status before proceeding.
    """
    # --- Guard: appointment must exist, belong to this patient, and be checked_in ---
    appt = db.query(Appointment).filter(
        Appointment.appointment_id == str(payload.appointment_id)
    ).first()
    if not appt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    if str(appt.patient_id) != str(payload.patient_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Appointment does not belong to this patient",
        )
    if appt.status != "checked_in":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Appointment must be in 'checked_in' status to start an encounter (current: {appt.status})",
        )
    # --- Delegate to stored procedure ---
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

    # Mark the linked appointment as completed (if any)
    if enc.appointment_id:
        appt = db.query(Appointment).filter(
            Appointment.appointment_id == str(enc.appointment_id)
        ).first()
        if appt and appt.status not in ("cancelled", "completed"):
            appt.status = "completed"

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

    # Pre-calculate BMI so trg_calculate_bmi has nothing to update
    bmi = None
    if payload.weight_kg and payload.height_cm and payload.height_cm > 0:
        bmi = round(payload.weight_kg / (payload.height_cm / 100.0) ** 2, 2)

    # Pre-calculate abnormal flag so trg_flag_abnormal_vitals has nothing to update
    is_abnormal = bool(
        (payload.heart_rate         is not None and (payload.heart_rate > 100 or payload.heart_rate < 60)) or
        (payload.blood_pressure_sys is not None and (payload.blood_pressure_sys > 140 or payload.blood_pressure_sys < 90)) or
        (payload.blood_pressure_dia is not None and payload.blood_pressure_dia > 90) or
        (payload.oxygen_saturation  is not None and payload.oxygen_saturation < 95) or
        (payload.temperature        is not None and (payload.temperature > 37.5 or payload.temperature < 36.0)) or
        (payload.respiratory_rate   is not None and (payload.respiratory_rate > 20 or payload.respiratory_rate < 12))
    )

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
        bmi                = bmi,
        is_abnormal        = is_abnormal,
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
