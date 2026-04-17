from uuid import UUID
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.care_plan import CarePlan
from app.schemas.care_plans import CarePlanCreate, CarePlanUpdate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_plan_or_404(db: Session, plan_id: UUID) -> CarePlan:
    plan = db.query(CarePlan).filter(CarePlan.plan_id == str(plan_id)).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Care plan not found")
    return plan


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_care_plan(
    db: Session,
    payload: CarePlanCreate,
    doctor_id: UUID,
) -> CarePlan:
    plan = CarePlan(
        patient_id    = str(payload.patient_id),
        doctor_id     = str(doctor_id),
        condition     = payload.condition,
        goals         = payload.goals,
        interventions = payload.interventions,
        start_date    = payload.start_date,
        review_date   = payload.review_date,
        notes         = payload.notes,
        status        = "active",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def list_care_plans(
    db: Session,
    patient_id:  Optional[UUID] = None,
    doctor_id:   Optional[UUID] = None,
    plan_status: Optional[str]  = None,
    skip:  int = 0,
    limit: int = 50,
) -> List[CarePlan]:
    q = db.query(CarePlan)
    if patient_id:
        q = q.filter(CarePlan.patient_id == str(patient_id))
    if doctor_id:
        q = q.filter(CarePlan.doctor_id == str(doctor_id))
    if plan_status:
        q = q.filter(CarePlan.status == plan_status)
    return q.order_by(CarePlan.created_at.desc()).offset(skip).limit(limit).all()


def get_care_plan(db: Session, plan_id: UUID) -> CarePlan:
    return _get_plan_or_404(db, plan_id)


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def update_care_plan(
    db: Session,
    plan_id: UUID,
    payload: CarePlanUpdate,
) -> CarePlan:
    plan = _get_plan_or_404(db, plan_id)

    if plan.status in ("completed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot update a care plan with status '{plan.status}'",
        )

    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(plan, field, value)
    plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)
    return plan
