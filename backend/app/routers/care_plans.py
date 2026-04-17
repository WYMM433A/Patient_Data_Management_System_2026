from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import require_permission
from app.schemas.care_plans import CarePlanCreate, CarePlanOut, CarePlanUpdate
from app.services import care_plan_service

router = APIRouter(prefix="/care-plans", tags=["Care Plans"])


@router.post("", response_model=CarePlanOut, status_code=status.HTTP_201_CREATED)
def create_care_plan(
    payload: CarePlanCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("manage_care_plans")),
):
    return care_plan_service.create_care_plan(db, payload, current_user.user_id)


@router.get("", response_model=List[CarePlanOut])
def list_care_plans(
    patient_id:  Optional[UUID] = None,
    doctor_id:   Optional[UUID] = None,
    plan_status: Optional[str]  = None,
    skip:  int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_permission("manage_care_plans")),
):
    return care_plan_service.list_care_plans(
        db,
        patient_id=patient_id,
        doctor_id=doctor_id,
        plan_status=plan_status,
        skip=skip,
        limit=limit,
    )


@router.get("/{plan_id}", response_model=CarePlanOut)
def get_care_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permission("manage_care_plans")),
):
    return care_plan_service.get_care_plan(db, plan_id)


@router.patch("/{plan_id}", response_model=CarePlanOut)
def update_care_plan(
    plan_id: UUID,
    payload: CarePlanUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("manage_care_plans")),
):
    return care_plan_service.update_care_plan(db, plan_id, payload)
