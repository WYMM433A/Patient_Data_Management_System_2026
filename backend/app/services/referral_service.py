from uuid import UUID
from typing import List, Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.referral import Referral
from app.models.encounter import Encounter
from app.schemas.referrals import ReferralCreate, ReferralStatusUpdate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_referral_or_404(db: Session, referral_id: UUID) -> Referral:
    ref = db.query(Referral).filter(
        Referral.referral_id == str(referral_id)
    ).first()
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")
    return ref


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

def create_referral(
    db: Session,
    encounter_id: UUID,
    payload: ReferralCreate,
    referred_by: UUID,
) -> Referral:
    enc = _get_encounter_or_404(db, encounter_id)
    if enc.status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot create a referral on a closed encounter",
        )

    ref = Referral(
        encounter_id = str(encounter_id),
        patient_id   = str(enc.patient_id),
        referred_by  = str(referred_by),
        specialty    = payload.specialty,
        reason       = payload.reason,
        urgency      = payload.urgency,
        status       = "pending",
        event_date   = payload.event_date,
    )
    db.add(ref)
    db.commit()
    db.refresh(ref)
    return ref


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def list_referrals(
    db: Session,
    encounter_id: Optional[UUID] = None,
    patient_id:   Optional[UUID] = None,
    ref_status:   Optional[str]  = None,
    skip:  int = 0,
    limit: int = 50,
) -> List[Referral]:
    q = db.query(Referral)
    if encounter_id:
        q = q.filter(Referral.encounter_id == str(encounter_id))
    if patient_id:
        q = q.filter(Referral.patient_id == str(patient_id))
    if ref_status:
        q = q.filter(Referral.status == ref_status)
    return q.order_by(Referral.referred_at.desc()).offset(skip).limit(limit).all()


def get_referral(db: Session, referral_id: UUID) -> Referral:
    return _get_referral_or_404(db, referral_id)


# ---------------------------------------------------------------------------
# Update status  (pending → accepted → completed)
# ---------------------------------------------------------------------------

def update_referral_status(
    db: Session,
    referral_id: UUID,
    payload: ReferralStatusUpdate,
) -> Referral:
    ref = _get_referral_or_404(db, referral_id)

    # Enforce forward-only transitions: pending→accepted→completed
    transitions = {"pending": {"accepted"}, "accepted": {"completed"}}
    allowed = transitions.get(ref.status, set())
    if payload.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition referral from '{ref.status}' to '{payload.status}'",
        )

    ref.status = payload.status
    db.commit()
    db.refresh(ref)
    return ref
