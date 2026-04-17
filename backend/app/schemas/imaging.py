from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import Optional
from datetime import datetime


VALID_IMAGING_TYPES = {"X-ray", "Ultrasound", "MRI", "CT", "ECG"}


class ImagingCreate(BaseModel):
    imaging_type:      Optional[str] = None
    body_part:         Optional[str] = None
    findings:          Optional[str] = None
    image_url:         Optional[str] = None
    radiologist_notes: Optional[str] = None
    event_date:        Optional[datetime] = None

    @field_validator("imaging_type")
    @classmethod
    def validate_imaging_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_IMAGING_TYPES:
            raise ValueError(f"imaging_type must be one of {sorted(VALID_IMAGING_TYPES)}")
        return v


class ImagingUpdate(BaseModel):
    findings:          Optional[str] = None
    radiologist_notes: Optional[str] = None
    image_url:         Optional[str] = None
    validated_at:      Optional[datetime] = None


class ImagingOut(BaseModel):
    imaging_id:        UUID
    patient_id:        UUID
    encounter_id:      UUID
    ordered_by:        UUID
    imaging_type:      Optional[str]
    body_part:         Optional[str]
    findings:          Optional[str]
    image_url:         Optional[str]
    radiologist_notes: Optional[str]
    performed_at:      datetime
    event_date:        Optional[datetime]
    validated_at:      Optional[datetime]

    model_config = {"from_attributes": True}
