"""
Enhanced Multi-Form Classifier
Combines data from multiple forms for comprehensive classification
"""

import google.generativeai as genai
import os
import json
from typing import Dict, List, Optional
from application_tracker import get_tracker, ApplicationStatus


class MultiFormClassifier:
    """
    Enhanced classifier that can work with:
    1. Single form (initial classification)
    2. Multiple forms (final comprehensive classification)
    """
    
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.tracker = get_tracker()
    
    def classify_single_form(self, student_data: Dict) -> Dict:
        """
        Initial classification based on a single form (Solicitud Oficial).
        This is the STAGE 1 classification - preliminary assessment.
        """
        prompt = self._build_single_form_prompt(student_data)
        
        try:
            response = self.model.generate_content(prompt)
            response_text = self._extract_response_text(response)
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            classification = json.loads(response_text)
            classification['classification_type'] = 'preliminary'
            classification['stage'] = 1
            
            print(f"[CLASSIFIER] Stage 1 - Preliminary: {classification['recommended_level']}")
            return classification
            
        except Exception as e:
            print(f"[CLASSIFIER] Stage 1 failed: {str(e)}")
            return self._get_fallback_classification()
    
    def classify_multi_form(self, email: str, student_data: Dict) -> Dict:
        """
        Final classification based on ALL submitted forms.
        This is the STAGE 2 classification - comprehensive assessment.
        
        Combines:
        - Solicitud Oficial (demographics, self-reported education)
        - Experiencia Ministerial (detailed ministry history)
        - Recomendación Pastoral (pastor verification)
        """
        app = self.tracker.get_application(email)
        
        if not app or not self.tracker.is_application_complete(email):
            print("[CLASSIFIER] Cannot do Stage 2 - application incomplete")
            return self.classify_single_form(student_data)
        
        # Build enriched prompt with ALL form data
        prompt = self._build_multi_form_prompt(app, student_data)
        
        try:
            response = self.model.generate_content(prompt)
            response_text = self._extract_response_text(response)
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            classification = json.loads(response_text)
            classification['classification_type'] = 'comprehensive'
            classification['stage'] = 2
            classification['forms_analyzed'] = len(app.forms_submitted)
            
            print(f"[CLASSIFIER] Stage 2 - Comprehensive: {classification['recommended_level']}")
            return classification
            
        except Exception as e:
            print(f"[CLASSIFIER] Stage 2 failed: {str(e)}")
            # Fall back to Stage 1
            return self.classify_single_form(student_data)
    
    def _build_single_form_prompt(self, student_data: Dict) -> str:
        """Build prompt for single-form classification (Stage 1)"""
        return f"""You are an academic advisor for Universidad Cristiana de Logos (UCL). Evaluate and recommend the appropriate academic level and program.

ACADEMIC LEVELS:
- Certificación Básica - Minimal formal education or new to theological studies
- Pregrado - Bachelor's level (requires secondary education)
- Postgrado - Master's level (requires undergraduate degree)
- Doctorado - Doctoral programs (requires master's degree)

AVAILABLE PROGRAMS:
CERTIFICACIÓN BÁSICA:
- Certificado en Estudios Bíblicos
- Certificado en Ministerio Cristiano

PREGRADO:
- Licenciatura en Teología
- Licenciatura en Ministerio Pastoral
- Licenciatura en Consejería Cristiana
- Licenciatura en Educación Cristiana
- Licenciatura en Liderazgo y Administración Ministerial

POSTGRADO:
- Maestría en Divinidad
- Maestría en Teología
- Maestría en Liderazgo Ministerial
- Maestría en Consejería Pastoral

DOCTORADO:
- Doctorado en Ministerio (D.Min)
- Doctorado en Teología (Th.D)

STUDENT DATA (PRELIMINARY - from initial form only):
Name: {student_data['applicant_name']}
Form: {student_data.get('form_name', 'N/A')}
Program Interest: {student_data['program_interest']}
Education Level: {student_data['education_level']}
Study Level Selected: {student_data.get('study_level_selected', 'N/A')}
Ministerial Experience: {student_data['ministerial_experience']}
Background: {student_data['background']}

NOTE: This is a PRELIMINARY assessment based on ONE form only. 
The applicant needs to submit additional forms (Experiencia Ministerial, Recomendación Pastoral) 
for a comprehensive evaluation.

Return ONLY valid JSON without any markdown formatting:
{{
  "recommended_level": "level here",
  "recommended_programs": ["program 1", "program 2"],
  "justification": "explanation here",
  "admissions_notes": "This is a PRELIMINARY recommendation. Applicant must submit: Formulario de Experiencia Ministerial and Formulario de Recomendación Pastoral for final evaluation.",
  "confidence_score": 6,
  "pending_documents": ["Experiencia Ministerial", "Recomendación Pastoral"]
}}"""
    
    def _build_multi_form_prompt(self, app, student_data: Dict) -> str:
        """Build prompt for multi-form classification (Stage 2)"""
        
        # Extract info from each form
        forms_data = {}
        for form_sub in app.forms_submitted:
            forms_data[form_sub.form_type] = {
                'form_name': form_sub.form_name,
                'submitted_at': form_sub.submitted_at,
                'data': form_sub.data_snapshot
            }
        
        # Build comprehensive prompt
        prompt = f"""You are an academic advisor for Universidad Cristiana de Logos (UCL). Perform a COMPREHENSIVE evaluation based on ALL submitted forms.

ACADEMIC LEVELS:
- Certificación Básica - Minimal formal education or new to theological studies
- Pregrado - Bachelor's level (requires secondary education)
- Postgrado - Master's level (requires undergraduate degree)
- Doctorado - Doctoral programs (requires master's degree)

AVAILABLE PROGRAMS:
CERTIFICACIÓN BÁSICA:
- Certificado en Estudios Bíblicos
- Certificado en Ministerio Cristiano

PREGRADO:
- Licenciatura en Teología
- Licenciatura en Ministerio Pastoral
- Licenciatura en Consejería Cristiana
- Licenciatura en Educación Cristiana
- Licenciatura en Liderazgo y Administración Ministerial

POSTGRADO:
- Maestría en Divinidad
- Maestría en Teología
- Maestría en Liderazgo Ministerial
- Maestría en Consejería Pastoral

DOCTORADO:
- Doctorado en Ministerio (D.Min)
- Doctorado en Teología (Th.D)

COMPREHENSIVE STUDENT DATA (from ALL forms):

FROM SOLICITUD OFICIAL:
Name: {student_data['applicant_name']}
Email: {student_data['email']}
Program Interest: {student_data['program_interest']}
Self-Reported Education: {student_data['education_level']}
Study Level Selected: {student_data.get('study_level_selected', 'N/A')}
Basic Ministry Info: {student_data['ministerial_experience']}

FORMS SUBMITTED:
{json.dumps(forms_data, indent=2, ensure_ascii=False)}

APPLICATION STATUS:
- Created: {app.created_at}
- Updated: {app.updated_at}
- Forms Submitted: {len(app.forms_submitted)}/{len(app.required_forms)}
- Status: {app.status}

IMPORTANT: This is a COMPREHENSIVE evaluation with ALL required forms submitted.
Consider:
1. Self-reported education vs documented education
2. Depth of ministry experience (from detailed form)
3. Pastoral recommendation strength
4. Consistency across all forms
5. Overall readiness for theological studies

Provide a FINAL classification recommendation that an admissions committee can act on.

Return ONLY valid JSON without any markdown formatting:
{{
  "recommended_level": "level here",
  "recommended_programs": ["program 1", "program 2"],
  "justification": "comprehensive explanation considering ALL forms",
  "admissions_notes": "Final recommendation for admissions committee. All required forms submitted.",
  "confidence_score": 9,
  "readiness_assessment": "detailed assessment of readiness for theological studies"
}}"""
        
        return prompt
    
    def _extract_response_text(self, response) -> str:
        """Safely extract text from Gemini response"""
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts') and candidate.content.parts:
                return candidate.content.parts[0].text
        return ""
    
    def _get_fallback_classification(self) -> Dict:
        """Fallback classification when AI fails"""
        return {
            "recommended_level": "Certificación Básica",
            "recommended_programs": ["Certificado en Estudios Bíblicos"],
            "justification": "Error en procesamiento automático. Requiere revisión manual.",
            "admissions_notes": "⚠️ ATENCIÓN: Clasificación automática falló. Revisar manualmente.",
            "confidence_score": 1,
            "classification_type": "fallback",
            "stage": 0
        }


def classify_student(student_data: Dict) -> Dict:
    """
    Main classification function (maintains backward compatibility).
    Automatically determines if this is Stage 1 or Stage 2 classification.
    """
    classifier = MultiFormClassifier()
    email = student_data.get('email')
    
    # Check if this is a complete application
    if email:
        tracker = get_tracker()
        if tracker.is_application_complete(email):
            print("[CLASSIFIER] Application complete - using Stage 2 (multi-form)")
            return classifier.classify_multi_form(email, student_data)
    
    # Default to Stage 1 (single form)
    print("[CLASSIFIER] Using Stage 1 (single-form) classification")
    return classifier.classify_single_form(student_data)