from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import Optional
from datetime import datetime


VALID_URGENCIES = {"routine", "urgent"}
VALID_STATUSES  = {"pending", "accepted", "completed"}


class ReferralCreate(BaseModel):
    specialty:  str
    reason:     Optional[str] = None
    urgency:    str = "routine"
    event_date: Optional[datetime] = None

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        if v not in VALID_URGENCIES:
            raise ValueError(f"urgency must be one of {sorted(VALID_URGENCIES)}")
        return v


class ReferralStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
        return v


class ReferralOut(BaseModel):
    referral_id:  UUID
    encounter_id: UUID
    patient_id:   UUID
    referred_by:  UUID
    specialty:    str
    reason:       Optional[str]
    urgency:      str
    status:       str
    referred_at:  datetime
    event_date:   Optional[datetime]

    model_config = {"from_attributes": True}
