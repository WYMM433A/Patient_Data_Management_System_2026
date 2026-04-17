from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


VALID_CATEGORIES = {"hematology", "biochemistry", "microbiology", "serology", "urinalysis", "imaging"}
VALID_PRIORITIES  = {"routine", "urgent", "stat"}
VALID_STATUSES    = {"ordered", "in-progress", "completed"}
VALID_ABNORMAL    = {"low", "borderline", "high", "critical"}


# ---------------------------------------------------------------------------
# Lab Test Templates (read-only, for browsing/selecting)
# ---------------------------------------------------------------------------

class LabTestParameterOut(BaseModel):
    parameter_id:      UUID
    parameter_name:    str
    display_order:     int
    unit:              Optional[str]
    normal_range_min:  Optional[Decimal]
    normal_range_max:  Optional[Decimal]
    normal_range_text: Optional[str]
    value_type:        str
    is_required:       bool

    model_config = {"from_attributes": True}


class LabTestTemplateOut(BaseModel):
    template_id:   UUID
    test_name:     str
    test_code:     str
    test_category: str
    description:   Optional[str]
    is_active:     bool

    model_config = {"from_attributes": True}


class LabTestTemplateDetailOut(LabTestTemplateOut):
    parameters: List[LabTestParameterOut] = []


# ---------------------------------------------------------------------------
# Lab Orders
# ---------------------------------------------------------------------------

class LabOrderCreate(BaseModel):
    template_id:   Optional[UUID] = None
    test_name:     str
    test_code:     Optional[str] = None
    test_category: Optional[str] = None
    priority:      str = "routine"
    event_date:    Optional[datetime] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}")
        return v

    @field_validator("test_category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_CATEGORIES:
            raise ValueError(f"test_category must be one of {VALID_CATEGORIES}")
        return v


class LabOrderStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        return v


class LabOrderOut(BaseModel):
    order_id:      UUID
    encounter_id:  UUID
    patient_id:    UUID
    ordered_by:    UUID
    template_id:   Optional[UUID]
    test_name:     str
    test_code:     Optional[str]
    test_category: Optional[str]
    priority:      str
    status:        str
    ordered_at:    datetime
    event_date:    Optional[datetime]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Lab Results
# ---------------------------------------------------------------------------

class LabResultCreate(BaseModel):
    parameter_id:    Optional[UUID] = None
    parameter_name:  str
    result_value:    str
    unit:            Optional[str] = None
    normal_range:    Optional[str] = None
    notes:           Optional[str] = None
    result_file_url: Optional[str] = None


class LabResultBulkCreate(BaseModel):
    """Submit all results for an order in one call."""
    results: List[LabResultCreate]


class LabResultOut(BaseModel):
    result_id:       UUID
    order_id:        UUID
    patient_id:      UUID
    parameter_id:    Optional[UUID]
    uploaded_by:     UUID
    parameter_name:  str
    result_value:    str
    unit:            Optional[str]
    normal_range:    Optional[str]
    is_abnormal:     bool
    abnormal_level:  Optional[str]
    notes:           Optional[str]
    result_file_url: Optional[str]
    resulted_at:     datetime
    validated_at:    Optional[datetime]
    validated_by:    Optional[UUID]

    model_config = {"from_attributes": True}
