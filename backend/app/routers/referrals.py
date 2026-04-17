from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import require_permission
from app.schemas.referrals import ReferralCreate, ReferralOut, ReferralStatusUpdate
from app.services import referral_service

router = APIRouter(tags=["Referrals"])


# ---------------------------------------------------------------------------
# Scoped under encounter
# ---------------------------------------------------------------------------

@router.post(
    "/encounters/{encounter_id}/referrals",
    response_model=ReferralOut,
    status_code=status.HTTP_201_CREATED,
)
def create_referral(
    encounter_id: UUID,
    payload: ReferralCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("create_referral")),
):
    return referral_service.create_referral(db, encounter_id, payload, current_user.user_id)


@router.get(
    "/encounters/{encounter_id}/referrals",
    response_model=List[ReferralOut],
)
def list_referrals_by_encounter(
    encounter_id: UUID,
    ref_status: Optional[str] = None,
    skip:  int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_permission("create_referral")),
):
    return referral_service.list_referrals(
        db, encounter_id=encounter_id, ref_status=ref_status, skip=skip, limit=limit
    )


# ---------------------------------------------------------------------------
# Global (filter by patient / status)
# ---------------------------------------------------------------------------

@router.get("/referrals", response_model=List[ReferralOut])
def list_referrals(
    patient_id: Optional[UUID] = None,
    ref_status: Optional[str]  = None,
    skip:  int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_permission("create_referral")),
):
    return referral_service.list_referrals(
        db, patient_id=patient_id, ref_status=ref_status, skip=skip, limit=limit
    )


@router.get("/referrals/{referral_id}", response_model=ReferralOut)
def get_referral(
    referral_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("create_referral")),
):
    return referral_service.get_referral(db, referral_id)


@router.patch("/referrals/{referral_id}/status", response_model=ReferralOut)
def update_referral_status(
    referral_id: UUID,
    payload: ReferralStatusUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("create_referral")),
):
    return referral_service.update_referral_status(db, referral_id, payload)
