from uuid import UUID
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from fastapi import HTTPException, status

from app.models.prescription import Prescription
from app.schemas.prescriptions import PrescriptionCreate, PrescriptionUpdate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_prescription_or_404(db: Session, prescription_id: UUID) -> Prescription:
    rx = db.query(Prescription).filter(
        Prescription.prescription_id == str(prescription_id),
        Prescription.is_removed == False,
    ).first()
    if not rx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")
    return rx


# ---------------------------------------------------------------------------
# Create  (delegates to usp_record_prescription — ACID + allergy check)
# ---------------------------------------------------------------------------

def create_prescription(
    db: Session,
    encounter_id: UUID,
    payload: PrescriptionCreate,
    current_user_id: UUID,
) -> Prescription:
    """
    Calls usp_record_prescription which:
      - Verifies the encounter is still open
      - Cross-checks patient allergies (exact case-insensitive match)
      - Inserts the prescription row atomically
      - Writes an audit log entry
    Raises HTTP 409 on allergy conflict or closed encounter.
    """
    sql = text("""
        DECLARE @new_id UNIQUEIDENTIFIER;
        EXEC usp_record_prescription
            @p_encounter_id    = :encounter_id,
            @p_patient_id      = :patient_id,
            @p_doctor_id       = :doctor_id,
            @p_drug_name       = :drug_name,
            @p_dosage          = :dosage,
            @p_frequency       = :frequency,
            @p_duration        = :duration,
            @p_route           = :route,
            @p_instructions    = :instructions,
            @p_prescription_id = @new_id OUTPUT;
        SELECT @new_id AS prescription_id;
    """)

    try:
        result = db.execute(sql, {
            "encounter_id": str(encounter_id),
            "patient_id":   str(payload.patient_id),
            "doctor_id":    str(payload.doctor_id),
            "drug_name":    payload.drug_name,
            "dosage":       payload.dosage,
            "frequency":    payload.frequency,
            "duration":     payload.duration,
            "route":        payload.route,
            "instructions": payload.instructions,
        })
        new_id = result.scalar()
        db.commit()
    except DBAPIError as exc:
        db.rollback()
        msg = str(exc.orig)
        if "ALLERGY_CONFLICT" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Allergy conflict: patient is allergic to '{payload.drug_name}'",
            )
        if "ENCOUNTER_CLOSED" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot prescribe on a closed encounter",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored procedure error: " + msg,
        )

    if not new_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored procedure did not return prescription_id",
        )

    rx = db.query(Prescription).filter(
        Prescription.prescription_id == str(new_id)
    ).first()
    if not rx:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prescription created but could not be fetched",
        )
    return rx


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def list_prescriptions(
    db: Session,
    encounter_id: Optional[UUID] = None,
    patient_id:   Optional[UUID] = None,
    active_only:  bool = False,
    skip:  int = 0,
    limit: int = 50,
) -> List[Prescription]:
    q = db.query(Prescription).filter(Prescription.is_removed == False)
    if encounter_id:
        q = q.filter(Prescription.encounter_id == str(encounter_id))
    if patient_id:
        q = q.filter(Prescription.patient_id == str(patient_id))
    if active_only:
        q = q.filter(Prescription.is_active == True)
    return q.order_by(Prescription.issued_at.desc()).offset(skip).limit(limit).all()


def get_prescription(db: Session, prescription_id: UUID) -> Prescription:
    return _get_prescription_or_404(db, prescription_id)


# ---------------------------------------------------------------------------
# Update  (discontinue / reactivate)
# ---------------------------------------------------------------------------

def update_prescription(
    db: Session,
    prescription_id: UUID,
    payload: PrescriptionUpdate,
) -> Prescription:
    rx = _get_prescription_or_404(db, prescription_id)
    rx.is_active = payload.is_active
    db.commit()
    db.refresh(rx)
    return rx
