"""
AI suggestion endpoints (ICD-10 and SOAP draft).
Requires create_encounter permission (doctors only).
"""

import logging
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.user import User
from app.schemas.ai import (
    ICDSuggestRequest,
    ICDSuggestResponse,
    SOAPDraftRequest,
    SOAPDraftResponse,
    AIErrorResponse,
)
from app.services.ai_service import get_ai_service
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai",
    tags=["AI Suggestions"],
    dependencies=[Depends(require_permission("create_encounter"))],
)


@router.post(
    "/icd-suggest",
    response_model=ICDSuggestResponse,
    responses={
        400: {"model": AIErrorResponse, "description": "Invalid input"},
        401: {"model": AIErrorResponse, "description": "Unauthorized"},
        403: {"model": AIErrorResponse, "description": "Forbidden"},
        500: {"model": AIErrorResponse, "description": "AI service error"},
    },
    summary="Suggest ICD-10 codes based on symptoms",
    description="Generate ICD-10 code suggestions from symptom text using AI. Suggestions only - doctor must verify.",
)
async def suggest_icd_codes(
    request: ICDSuggestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ICDSuggestResponse:
    """
    Suggest ICD-10 codes based on patient symptoms.
    
    **Requires:** create_encounter permission (doctors)
    
    **Input:** Symptom/chief complaint text
    **Output:** List of suggested ICD-10 codes with confidence scores
    **Important:** Suggestions are for reference only. Physician must verify and select appropriate codes.
    """
    try:
        # Call AI service
        ai_service = get_ai_service()
        result = ai_service.suggest_icd_codes(request.text)

        # Log to audit trail
        try:
            audit_log = AuditLog(
                user_id=current_user.user_id,
                action="AI_ICD_SUGGEST",
                table_name="encounters",
                record_id=None,
                old_values=None,
                new_values={"text_length": len(request.text), "suggestions_count": len(result.codes)},
            )
            db.add(audit_log)
            db.commit()
        except Exception as audit_err:
            logger.warning(f"Failed to log AI_ICD_SUGGEST action: {audit_err}")
            # Don't fail the API call if audit logging fails

        logger.info(
            f"ICD suggest: user={current_user.username}, codes={len(result.codes)}"
        )
        return result

    except ValueError as e:
        logger.error(f"Invalid input for ICD suggest: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error in ICD suggest endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service is currently unavailable. Please try again later.",
        )


@router.post(
    "/soap-draft",
    response_model=SOAPDraftResponse,
    responses={
        400: {"model": AIErrorResponse, "description": "Invalid input"},
        401: {"model": AIErrorResponse, "description": "Unauthorized"},
        403: {"model": AIErrorResponse, "description": "Forbidden"},
        500: {"model": AIErrorResponse, "description": "AI service error"},
    },
    summary="Generate SOAP note draft",
    description="Generate a SOAP note draft based on clinical context. Doctor must review and refine.",
)
async def draft_soap_note(
    request: SOAPDraftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SOAPDraftResponse:
    """
    Generate a SOAP note draft based on clinical context.
    
    **Requires:** create_encounter permission (doctors)
    
    **Input:** Chief complaint, vitals, allergies, medical history
    **Output:** SOAP note draft (Subjective, Objective, Assessment, Plan)
    **Important:** AI-generated content is a draft for physician review. Physician must verify all information.
    """
    try:
        # Call AI service
        ai_service = get_ai_service()
        result = ai_service.draft_soap_note(
            chief_complaint=request.chief_complaint,
            vitals=request.vitals,
            allergies=request.allergies,
            medical_history=request.medical_history,
        )

        # Log to audit trail
        try:
            audit_log = AuditLog(
                user_id=current_user.user_id,
                action="AI_SOAP_DRAFT",
                table_name="encounters",
                record_id=None,
                old_values=None,
                new_values={
                    "chief_complaint_length": len(request.chief_complaint),
                    "has_vitals": request.vitals is not None,
                    "allergies_count": len(request.allergies),
                    "history_count": len(request.medical_history),
                },
            )
            db.add(audit_log)
            db.commit()
        except Exception as audit_err:
            logger.warning(f"Failed to log AI_SOAP_DRAFT action: {audit_err}")
            # Don't fail the API call if audit logging fails

        logger.info(
            f"SOAP draft: user={current_user.username}, chief_complaint_len={len(request.chief_complaint)}"
        )
        return result

    except ValueError as e:
        logger.error(f"Invalid input for SOAP draft: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error in SOAP draft endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service is currently unavailable. Please try again later.",
        )
        
class PatientSummaryRequest(BaseModel):
    patient_name: str
    age: int | str
    gender: str
    blood_type: str
    medical_history: str
    allergies: str
    vaccinations: str
    recent_encounters: str

@router.post("/patient-summary")
async def patient_summary(
    request: PatientSummaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prompt = f"""You are a clinical assistant. Give a brief 5-8 sentence patient summary 
for a doctor about to see this patient. Be concise, clinically relevant, and highlight 
anything important the doctor should know before the consultation.

Patient: {request.patient_name}, {request.age} years old, {request.gender}, Blood type: {request.blood_type}
Medical History: {request.medical_history}
Allergies: {request.allergies}
Vaccinations: {request.vaccinations}
Recent Encounters (last 3):
{request.recent_encounters}

Write a flowing paragraph summary — no bullet points, no headers, just clear clinical prose."""

    try:
        ai_service = get_ai_service()
        response = ai_service.client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        summary = response.text.strip()

        # Audit log
        try:
            audit_log = AuditLog(
                user_id=current_user.user_id,
                action="AI_PATIENT_SUMMARY",
                table_name="patients",
                record_id=None,
                old_values=None,
                new_values={"patient_name": request.patient_name},
            )
            db.add(audit_log)
            db.commit()
        except Exception:
            pass

        return {"summary": summary}

    except Exception as e:
        logger.error(f"Gemini error in patient_summary: {str(e)}")
        raise HTTPException(status_code=500, detail="AI service unavailable")
