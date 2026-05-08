"""
AI service for Gemini-powered suggestions.
Handles ICD-10 code suggestions and SOAP note drafting.
"""

import json
import time
import logging
from typing import List
import google.genai as genai

from app.config import settings
from app.schemas.ai import ICDCode, ICDSuggestResponse, SOAPDraftResponse, VitalsInfo

logger = logging.getLogger(__name__)

# Configure Gemini API



class AIService:
    """Service for AI-powered clinical suggestions via Gemini."""

    def __init__(self):
        from google.genai import types
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(api_version='v1beta'))

    def suggest_icd_codes(self, symptom_text: str) -> ICDSuggestResponse:
        """
        Generate ICD-10 code suggestions based on symptom description.
        
        Args:
            symptom_text: Description of symptoms/chief complaint
            
        Returns:
            ICDSuggestResponse with suggested codes
            
        Raises:
            Exception: If Gemini API fails
        """
        try:
            prompt = f"""You are a medical coding expert. Based on the following symptom description, 
suggest up to 5 relevant ICD-10 codes that a physician might consider.

Symptom/Chief Complaint: {symptom_text}

Return ONLY a valid JSON object with this exact structure (no markdown, no code blocks):
{{
    "codes": [
        {{"code": "R07.9", "description": "Chest pain, unspecified", "confidence": 0.95}},
        {{"code": "R06.02", "description": "Shortness of breath", "confidence": 0.90}}
    ]
}}

IMPORTANT:
- Return valid JSON only
- Include 'code' (ICD-10), 'description', and 'confidence' (0-1 float) for each
- Return 3-5 codes maximum
- Do not include explanatory text or markdown formatting"""

            for attempt in range(3):
                try:
                    response = self.client.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=prompt
                    )
                    break
                except Exception as e:
                    if "503" in str(e) and attempt < 2:
                        time.sleep(2)
                        continue
                    raise

            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            # Parse JSON response
            data = json.loads(response_text)
            codes = [ICDCode(**code) for code in data.get("codes", [])]

            logger.info(f"ICD suggest: {len(codes)} codes generated for text: {symptom_text[:50]}...")
            
            return ICDSuggestResponse(codes=codes)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            raise ValueError(f"AI service returned invalid response: {str(e)}")
        except Exception as e:
            logger.error(f"Gemini API error in suggest_icd_codes: {str(e)}")
            raise

    def draft_soap_note(
        self,
        chief_complaint: str,
        vitals: VitalsInfo = None,
        allergies: List[str] = None,
        medical_history: List[str] = None
    ) -> SOAPDraftResponse:
        """
        Generate a SOAP note draft based on clinical context.
        
        Args:
            chief_complaint: Patient's chief complaint
            vitals: Vital signs measurements
            allergies: Known allergies list
            medical_history: Relevant medical history
            
        Returns:
            SOAPDraftResponse with S/O/A/P sections
            
        Raises:
            Exception: If Gemini API fails
        """
        try:
            # Format vitals for prompt
            vitals_str = "No vitals recorded"
            if vitals:
                vitals_dict = vitals.model_dump(exclude_none=True)
                vitals_str = ", ".join([f"{k}: {v}" for k, v in vitals_dict.items()])

            # Format allergies
            allergies_str = "NKDA" if not allergies else ", ".join(allergies)

            # Format medical history
            history_str = "None reported" if not medical_history else ", ".join(medical_history)

            prompt = f"""You are an experienced physician. Draft a concise SOAP note based on the following clinical context.
The output should be professional, clinically sound, and appropriate for a medical record.

Chief Complaint: {chief_complaint}
Vitals: {vitals_str}
Allergies: {allergies_str}
Medical History: {history_str}

Return ONLY a valid JSON object with this exact structure (no markdown, no code blocks):
{{
    "subjective": "Patient reports [main symptom] for [duration]. [One associated finding or denial].",
"objective": "Vitals: [key vitals only]. [One exam finding or deferred].",
"assessment": "[Top 1-2 diagnoses only]. [Brief reasoning in one sentence].",
"plan": "[Top 3 actions only — test, medication, follow-up]."

}}

IMPORTANT:
- Return valid JSON only
- Be clinically appropriate and evidence-based
- Be brief and clinical — this is a draft, not a final note
- Keep each section to 2 sentences maximum, be concise and direct
- List plan items separated by commas, not full sentences
- Include vital signs in Objective section
- Suggest relevant labs/imaging if appropriate
- Do not include explanatory text or markdown formatting
- All sections should be clear and physician-appropriate"""

            for attempt in range(3):
                try:
                    response = self.client.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=prompt
                    )
                    break
                except Exception as e:
                    if "503" in str(e) and attempt < 2:
                        time.sleep(2)
                        continue
                    raise
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            # Parse JSON response
            data = json.loads(response_text)
            
            soap_response = SOAPDraftResponse(
                subjective=data.get("subjective", ""),
                objective=data.get("objective", ""),
                assessment=data.get("assessment", ""),
                plan=data.get("plan", "")
            )

            logger.info(f"SOAP draft generated for chief complaint: {chief_complaint[:50]}...")
            
            return soap_response

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            raise ValueError(f"AI service returned invalid response: {str(e)}")
        except Exception as e:
            logger.error(f"Gemini API error in draft_soap_note: {str(e)}")
            raise


# Singleton instance
_ai_service = None


def get_ai_service() -> AIService:
    """Get or create AI service instance."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
