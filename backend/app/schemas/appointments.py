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
    patient_name:   Optional[str] = None
    doctor_name:    Optional[str] = None
    scheduled_at:   datetime
    reason:         Optional[str] = None
    status:         str
    notes:          Optional[str] = None
    checked_at:     Optional[datetime] = None
    created_by:     UUID
    created_at:     datetime

    @classmethod
    def from_orm_with_names(cls, appt) -> "AppointmentOut":
        obj = cls.model_validate(appt)
        if appt.patient:
            obj.patient_name = f"{appt.patient.first_name} {appt.patient.last_name}"
        if appt.doctor:
            obj.doctor_name = f"{appt.doctor.first_name} {appt.doctor.last_name}"
        return obj

    model_config = {"from_attributes": True}
