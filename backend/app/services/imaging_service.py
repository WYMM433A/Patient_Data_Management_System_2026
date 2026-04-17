from uuid import UUID
from typing import List, Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.imaging import ImagingRecord
from app.models.encounter import Encounter
from app.schemas.imaging import ImagingCreate, ImagingUpdate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_record_or_404(db: Session, imaging_id: UUID) -> ImagingRecord:
    record = db.query(ImagingRecord).filter(
        ImagingRecord.imaging_id == str(imaging_id)
    ).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imaging record not found")
    return record


def _get_encounter_or_404(db: Session, encounter_id: UUID) -> Encounter:
    enc = db.query(Encounter).filter(
        Encounter.encounter_id == str(encounter_id)
    ).first()
    if not enc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")
    return enc


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_imaging(
    db: Session,
    encounter_id: UUID,
    payload: ImagingCreate,
    ordered_by: UUID,
) -> ImagingRecord:
    enc = _get_encounter_or_404(db, encounter_id)
    # No open-encounter guard: radiology studies are often performed
    # and reported after the encounter is already closed.

    record = ImagingRecord(
        patient_id        = str(enc.patient_id),
        encounter_id      = str(encounter_id),
        ordered_by        = str(ordered_by),
        imaging_type      = payload.imaging_type,
        body_part         = payload.body_part,
        findings          = payload.findings,
        image_url         = payload.image_url,
        radiologist_notes = payload.radiologist_notes,
        event_date        = payload.event_date,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def list_imaging(
    db: Session,
    encounter_id:  Optional[UUID] = None,
    patient_id:    Optional[UUID] = None,
    imaging_type:  Optional[str]  = None,
    skip:  int = 0,
    limit: int = 50,
) -> List[ImagingRecord]:
    q = db.query(ImagingRecord)
    if encounter_id:
        q = q.filter(ImagingRecord.encounter_id == str(encounter_id))
    if patient_id:
        q = q.filter(ImagingRecord.patient_id == str(patient_id))
    if imaging_type:
        q = q.filter(ImagingRecord.imaging_type == imaging_type)
    return q.order_by(ImagingRecord.performed_at.desc()).offset(skip).limit(limit).all()


def get_imaging(db: Session, imaging_id: UUID) -> ImagingRecord:
    return _get_record_or_404(db, imaging_id)


# ---------------------------------------------------------------------------
# Update  (radiologist fills findings / notes after study is performed)
# ---------------------------------------------------------------------------

def update_imaging(
    db: Session,
    imaging_id: UUID,
    payload: ImagingUpdate,
) -> ImagingRecord:
    record = _get_record_or_404(db, imaging_id)
    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record
