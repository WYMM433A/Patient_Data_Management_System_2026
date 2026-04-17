from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import Optional
from datetime import datetime, date


VALID_STATUSES = {"active", "completed", "cancelled"}


class CarePlanCreate(BaseModel):
    patient_id:    UUID
    condition:     str
    goals:         Optional[str] = None
    interventions: Optional[str] = None
    start_date:    date
    review_date:   Optional[date] = None
    notes:         Optional[str] = None


class CarePlanUpdate(BaseModel):
    goals:         Optional[str] = None
    interventions: Optional[str] = None
    review_date:   Optional[date] = None
    notes:         Optional[str] = None
    status:        Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
        return v


class CarePlanOut(BaseModel):
    plan_id:       UUID
    patient_id:    UUID
    doctor_id:     UUID
    condition:     str
    goals:         Optional[str]
    interventions: Optional[str]
    start_date:    date
    review_date:   Optional[date]
    status:        str
    notes:         Optional[str]
    created_at:    datetime
    updated_at:    Optional[datetime]

    model_config = {"from_attributes": True}
