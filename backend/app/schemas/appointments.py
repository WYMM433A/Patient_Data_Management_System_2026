from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import Optional
from datetime import datetime


class AppointmentCreate(BaseModel):
    patient_id:   UUID
    doctor_id:    UUID
    scheduled_at: datetime
    reason:       Optional[str] = None
    notes:        Optional[str] = None

    @field_validator("status", mode="before", check_fields=False)
    @classmethod
    def _noop(cls, v):
        return v


class AppointmentUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    reason:       Optional[str]      = None
    notes:        Optional[str]      = None
    status:       Optional[str]      = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        allowed = {"scheduled", "confirmed", "checked_in", "completed", "cancelled"}
        if v is not None and v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class AppointmentOut(BaseModel):
    appointment_id: UUID
    patient_id:     UUID
    doctor_id:      UUID
    scheduled_at:   datetime
    reason:         Optional[str] = None
    status:         str
    notes:          Optional[str] = None
    checked_at:     Optional[datetime] = None
    created_by:     UUID
    created_at:     datetime

    model_config = {"from_attributes": True}
