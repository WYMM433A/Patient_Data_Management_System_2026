"""
AI suggestion schemas for ICD-10 and SOAP draft generation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ICD-10 Suggestion Schemas
class ICDSuggestRequest(BaseModel):
    """Request for ICD-10 code suggestions based on symptom text."""
    text: str = Field(..., min_length=5, max_length=1000, description="Symptom/complaint text to analyze")

    class Config:
        schema_extra = {
            "example": {
                "text": "patient presents with chest pain and shortness of breath"
            }
        }


class ICDCode(BaseModel):
    """Single ICD-10 code suggestion."""
    code: str = Field(..., description="ICD-10 code")
    description: str = Field(..., description="Description of the code")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence score 0-1")

    class Config:
        schema_extra = {
            "example": {
                "code": "R07.9",
                "description": "Chest pain, unspecified",
                "confidence": 0.95
            }
        }


class ICDSuggestResponse(BaseModel):
    """Response with suggested ICD-10 codes."""
    codes: List[ICDCode] = Field(..., description="List of suggested ICD-10 codes")
    disclaimer: str = Field(
        default="AI suggestions are for reference only. Doctor must verify and select appropriate codes.",
        description="Clinical disclaimer"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "codes": [
                    {"code": "R07.9", "description": "Chest pain, unspecified", "confidence": 0.95},
                    {"code": "R06.02", "description": "Shortness of breath", "confidence": 0.92},
                ],
                "disclaimer": "AI suggestions are for reference only. Doctor must verify and select appropriate codes."
            }
        }


# SOAP Draft Schemas
class VitalsInfo(BaseModel):
    """Vital signs information for SOAP draft."""
    temperature: Optional[float] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    bmi: Optional[float] = None

    class Config:
        schema_extra = {
            "example": {
                "temperature": 98.6,
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "heart_rate": 72,
                "respiratory_rate": 16,
                "oxygen_saturation": 98.0,
                "weight": 70.0,
                "height": 170.0,
                "bmi": 24.2
            }
        }


class SOAPDraftRequest(BaseModel):
    """Request for AI-generated SOAP note draft."""
    chief_complaint: str = Field(..., min_length=3, max_length=500, description="Chief complaint")
    vitals: Optional[VitalsInfo] = Field(None, description="Current vital signs")
    allergies: List[str] = Field(default_factory=list, description="Known allergies")
    medical_history: List[str] = Field(default_factory=list, description="Relevant medical history")

    class Config:
        schema_extra = {
            "example": {
                "chief_complaint": "Chest pain and shortness of breath for 2 days",
                "vitals": {
                    "temperature": 98.6,
                    "systolic_bp": 130,
                    "diastolic_bp": 85,
                    "heart_rate": 88,
                    "respiratory_rate": 18,
                    "oxygen_saturation": 96.0
                },
                "allergies": ["Penicillin"],
                "medical_history": ["Hypertension", "Type 2 Diabetes"]
            }
        }


class SOAPDraftResponse(BaseModel):
    """Response with AI-generated SOAP note draft."""
    subjective: str = Field(..., description="Subjective section of SOAP note")
    objective: str = Field(..., description="Objective section of SOAP note (physical exam, vitals)")
    assessment: str = Field(..., description="Assessment section (diagnosis/impression)")
    plan: str = Field(..., description="Plan section (treatment/follow-up)")
    disclaimer: str = Field(
        default="AI-generated content is a draft for physician review and refinement. Physician must verify all information and clinical judgment applies.",
        description="Clinical disclaimer"
    )

    class Config:
        schema_extra = {
            "example": {
                "subjective": "Patient reports chest pain and shortness of breath that started 2 days ago. Associated with exertion. Denies fever or cough.",
                "objective": "Vitals: BP 130/85, HR 88, RR 18, O2 98%. Lungs clear to auscultation bilaterally. Cardiac: regular rate and rhythm.",
                "assessment": "Chest pain with dyspnea, likely cardiac etiology. Differential includes angina, atypical MI, or musculoskeletal pain.",
                "plan": "Obtain EKG and troponin. Chest X-ray. Consider cardiology consultation. Start cardiac monitoring. Pain management as needed.",
                "disclaimer": "AI-generated content is a draft for physician review and refinement. Physician must verify all information and clinical judgment applies."
            }
        }


class AIErrorResponse(BaseModel):
    """Error response from AI endpoints."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")

    class Config:
        schema_extra = {
            "example": {
                "error": "AI service unavailable",
                "detail": "Gemini API is currently unavailable. Please try again later."
            }
        }
