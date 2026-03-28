from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional, List
from datetime import date, datetime


# ---------- Patient ----------

class PatientCreate(BaseModel):
    first_name:              str
    last_name:               str
    date_of_birth:           date
    gender:                  Optional[str]  = None
    blood_type:              Optional[str]  = None
    phone:                   Optional[str]  = None
    email:                   Optional[str]  = None
    address:                 Optional[str]  = None
    emergency_contact_name:  Optional[str]  = None
    emergency_contact_phone: Optional[str]  = None


class PatientUpdate(BaseModel):
    first_name:              Optional[str]  = None
    last_name:               Optional[str]  = None
    date_of_birth:           Optional[date] = None
    gender:                  Optional[str]  = None
    blood_type:              Optional[str]  = None
    phone:                   Optional[str]  = None
    email:                   Optional[str]  = None
    address:                 Optional[str]  = None
    emergency_contact_name:  Optional[str]  = None
    emergency_contact_phone: Optional[str]  = None


class PatientOut(BaseModel):
    patient_id:              UUID
    mrn:                     str
    first_name:              str
    last_name:               str
    date_of_birth:           date
    gender:                  Optional[str]  = None
    blood_type:              Optional[str]  = None
    phone:                   Optional[str]  = None
    email:                   Optional[str]  = None
    address:                 Optional[str]  = None
    emergency_contact_name:  Optional[str]  = None
    emergency_contact_phone: Optional[str]  = None
    created_at:              datetime

    model_config = {"from_attributes": True}


# ---------- Medical History ----------

class MedicalHistoryCreate(BaseModel):
    condition_name: str
    icd_code:       Optional[str]  = None
    onset_date:     Optional[date] = None
    is_chronic:     bool           = False
    notes:          Optional[str]  = None


class MedicalHistoryOut(BaseModel):
    history_id:      UUID
    patient_id:      UUID
    condition_name:  str
    icd_code:        Optional[str]  = None
    onset_date:      Optional[date] = None
    resolution_date: Optional[date] = None
    is_chronic:      bool
    notes:           Optional[str]  = None
    recorded_at:     datetime

    model_config = {"from_attributes": True}


# ---------- Allergy ----------

class AllergyCreate(BaseModel):
    allergen:      str
    reaction_type: Optional[str] = None
    severity:      Optional[str] = None


class AllergyOut(BaseModel):
    allergy_id:    UUID
    patient_id:    UUID
    allergen:      str
    reaction_type: Optional[str] = None
    severity:      Optional[str] = None
    recorded_at:   datetime

    model_config = {"from_attributes": True}


# ---------- Vaccination ----------

class VaccinationCreate(BaseModel):
    vaccine_name:    str
    dose_number:     Optional[int]  = None
    administered_at: date
    next_due_date:   Optional[date] = None
    notes:           Optional[str]  = None


class VaccinationOut(BaseModel):
    vaccination_id:  UUID
    patient_id:      UUID
    vaccine_name:    str
    dose_number:     Optional[int]  = None
    administered_at: date
    next_due_date:   Optional[date] = None
    notes:           Optional[str]  = None
    recorded_at:     datetime

    model_config = {"from_attributes": True}
