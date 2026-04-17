from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import Optional
from datetime import datetime


VALID_ROUTES = {"oral", "IV", "topical", "inhaled", "subcutaneous"}


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class PrescriptionCreate(BaseModel):
    patient_id:   UUID
    doctor_id:    UUID
    drug_name:    str
    dosage:       Optional[str] = None
    frequency:    Optional[str] = None
    duration:     Optional[str] = None
    route:        Optional[str] = None
    instructions: Optional[str] = None
    event_date:   Optional[datetime] = None

    @field_validator("route")
    @classmethod
    def validate_route(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_ROUTES:
            raise ValueError(f"route must be one of {VALID_ROUTES}")
        return v


# ---------------------------------------------------------------------------
# Update (discontinue or reactivate)
# ---------------------------------------------------------------------------

class PrescriptionUpdate(BaseModel):
    is_active: bool


# ---------------------------------------------------------------------------
# Out
# ---------------------------------------------------------------------------

class PrescriptionOut(BaseModel):
    prescription_id: UUID
    encounter_id:    UUID
    patient_id:      UUID
    doctor_id:       UUID
    drug_name:       str
    dosage:          Optional[str]
    frequency:       Optional[str]
    duration:        Optional[str]
    route:           Optional[str]
    instructions:    Optional[str]
    is_active:       bool
    issued_at:       datetime
    event_date:      Optional[datetime]
    validated_at:    Optional[datetime]

    model_config = {"from_attributes": True}
