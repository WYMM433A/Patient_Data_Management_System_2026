from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import require_permission
from app.schemas.prescriptions import PrescriptionCreate, PrescriptionOut, PrescriptionUpdate
from app.services import prescription_service

router = APIRouter(tags=["Prescriptions"])


# ---------------------------------------------------------------------------
# Scoped under a specific encounter
# ---------------------------------------------------------------------------

@router.post(
    "/encounters/{encounter_id}/prescriptions",
    response_model=PrescriptionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_prescription(
    encounter_id: UUID,
    payload: PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("issue_prescription")),
):
    return prescription_service.create_prescription(db, encounter_id, payload, current_user.user_id)


@router.get(
    "/encounters/{encounter_id}/prescriptions",
    response_model=List[PrescriptionOut],
)
def list_prescriptions_by_encounter(
    encounter_id: UUID,
    active_only: bool = False,
    skip:  int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_permission("issue_prescription")),
):
    return prescription_service.list_prescriptions(
        db, encounter_id=encounter_id, active_only=active_only, skip=skip, limit=limit
    )


# ---------------------------------------------------------------------------
# Scoped globally (e.g., all prescriptions for a patient)
# ---------------------------------------------------------------------------

@router.get(
    "/prescriptions",
    response_model=List[PrescriptionOut],
)
def list_prescriptions(
    patient_id:  Optional[UUID] = None,
    active_only: bool = False,
    skip:  int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_permission("issue_prescription")),
):
    return prescription_service.list_prescriptions(
        db, patient_id=patient_id, active_only=active_only, skip=skip, limit=limit
    )


@router.get(
    "/prescriptions/{prescription_id}",
    response_model=PrescriptionOut,
)
def get_prescription(
    prescription_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("issue_prescription")),
):
    return prescription_service.get_prescription(db, prescription_id)


@router.patch(
    "/prescriptions/{prescription_id}",
    response_model=PrescriptionOut,
)
def update_prescription(
    prescription_id: UUID,
    payload: PrescriptionUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("issue_prescription")),
):
    return prescription_service.update_prescription(db, prescription_id, payload)
