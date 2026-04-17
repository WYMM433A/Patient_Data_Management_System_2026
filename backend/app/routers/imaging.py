from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import require_permission
from app.schemas.imaging import ImagingCreate, ImagingOut, ImagingUpdate
from app.services import imaging_service

router = APIRouter(tags=["Imaging"])


# ---------------------------------------------------------------------------
# Scoped under encounter
# ---------------------------------------------------------------------------

@router.post(
    "/encounters/{encounter_id}/imaging",
    response_model=ImagingOut,
    status_code=status.HTTP_201_CREATED,
)
def create_imaging(
    encounter_id: UUID,
    payload: ImagingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("record_imaging")),
):
    return imaging_service.create_imaging(db, encounter_id, payload, current_user.user_id)


@router.get(
    "/encounters/{encounter_id}/imaging",
    response_model=List[ImagingOut],
)
def list_imaging_by_encounter(
    encounter_id: UUID,
    imaging_type: Optional[str] = None,
    skip:  int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_permission("record_imaging")),
):
    return imaging_service.list_imaging(
        db,
        encounter_id=encounter_id,
        imaging_type=imaging_type,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Global (filter by patient / type)
# ---------------------------------------------------------------------------

@router.get("/imaging", response_model=List[ImagingOut])
def list_imaging(
    patient_id:   Optional[UUID] = None,
    imaging_type: Optional[str]  = None,
    skip:  int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_permission("record_imaging")),
):
    return imaging_service.list_imaging(
        db,
        patient_id=patient_id,
        imaging_type=imaging_type,
        skip=skip,
        limit=limit,
    )


@router.get("/imaging/{imaging_id}", response_model=ImagingOut)
def get_imaging(
    imaging_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("record_imaging")),
):
    return imaging_service.get_imaging(db, imaging_id)


@router.patch("/imaging/{imaging_id}", response_model=ImagingOut)
def update_imaging(
    imaging_id: UUID,
    payload: ImagingUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("record_imaging")),
):
    return imaging_service.update_imaging(db, imaging_id, payload)
