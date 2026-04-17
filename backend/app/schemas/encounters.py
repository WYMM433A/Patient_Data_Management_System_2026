from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import Optional, List
from datetime import datetime, date


# ---------------------------------------------------------------------------
# Encounter
# ---------------------------------------------------------------------------

class EncounterCreate(BaseModel):
    patient_id:      UUID
    doctor_id:       UUID
    appointment_id:  Optional[UUID] = None
    encounter_type:  str
    chief_complaint: Optional[str] = None

    @field_validator("encounter_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"outpatient", "follow-up", "emergency"}
        if v not in allowed:
            raise ValueError(f"encounter_type must be one of {allowed}")
        return v


class EncounterOut(BaseModel):
    encounter_id:    UUID
    patient_id:      UUID
    doctor_id:       UUID
    appointment_id:  Optional[UUID]
    encounter_date:  datetime
    encounter_type:  str
    chief_complaint: Optional[str]
    status:          str
    visit_number:    int
    created_at:      datetime
    closed_at:       Optional[datetime]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# SOAP Note
# ---------------------------------------------------------------------------

class SOAPNoteUpdate(BaseModel):
    subjective: Optional[str] = None
    objective:  Optional[str] = None
    assessment: Optional[str] = None
    plan:       Optional[str] = None
    event_date: Optional[datetime] = None


class SOAPNoteOut(BaseModel):
    note_id:      UUID
    encounter_id: UUID
    doctor_id:    UUID
    subjective:   Optional[str]
    objective:    Optional[str]
    assessment:   Optional[str]
    plan:         Optional[str]
    recorded_at:  datetime
    event_date:   Optional[datetime]
    validated_at: Optional[datetime]
    updated_at:   Optional[datetime]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Vitals
# ---------------------------------------------------------------------------

class VitalsCreate(BaseModel):
    blood_pressure_sys: Optional[int]   = None
    blood_pressure_dia: Optional[int]   = None
    heart_rate:         Optional[int]   = None
    temperature:        Optional[float] = None
    weight_kg:          Optional[float] = None
    height_cm:          Optional[float] = None
    oxygen_saturation:  Optional[int]   = None
    respiratory_rate:   Optional[int]   = None
    event_date:         Optional[datetime] = None


class VitalsOut(BaseModel):
    vital_id:           UUID
    patient_id:         UUID
    encounter_id:       UUID
    recorded_by:        UUID
    blood_pressure_sys: Optional[int]
    blood_pressure_dia: Optional[int]
    heart_rate:         Optional[int]
    temperature:        Optional[float]
    weight_kg:          Optional[float]
    height_cm:          Optional[float]
    oxygen_saturation:  Optional[int]
    respiratory_rate:   Optional[int]
    bmi:                Optional[float]
    is_abnormal:        bool
    recorded_at:        datetime
    event_date:         Optional[datetime]
    validated_at:       Optional[datetime]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Diagnoses
# ---------------------------------------------------------------------------

class DiagnosisCreate(BaseModel):
    icd_code:       str
    description:    Optional[str] = None
    diagnosis_type: str                    # primary | secondary
    condition:      Optional[str] = None   # suspected | confirmed | excluded | recurrent
    timing:         Optional[str] = None   # acute | chronic | complication | recurrence
    is_chronic:     bool = False
    event_date:     Optional[date] = None

    @field_validator("diagnosis_type")
    @classmethod
    def validate_dtype(cls, v: str) -> str:
        if v not in {"primary", "secondary"}:
            raise ValueError("diagnosis_type must be primary or secondary")
        return v

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in {"suspected", "confirmed", "excluded", "recurrent"}:
            raise ValueError("condition must be suspected, confirmed, excluded, or recurrent")
        return v

    @field_validator("timing")
    @classmethod
    def validate_timing(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in {"acute", "chronic", "complication", "recurrence"}:
            raise ValueError("timing must be acute, chronic, complication, or recurrence")
        return v


class DiagnosisOut(BaseModel):
    diagnosis_id:   UUID
    encounter_id:   UUID
    patient_id:     UUID
    icd_code:       str
    description:    Optional[str]
    diagnosis_type: str
    condition:      Optional[str]
    timing:         Optional[str]
    is_chronic:     bool
    diagnosed_by:   UUID
    recorded_at:    datetime
    event_date:     Optional[date]
    validated_at:   Optional[datetime]

    model_config = {"from_attributes": True}
