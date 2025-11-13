import google.generativeai as genai
import os
import json

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def classify_student(student_data):
    prompt = f"""You are an academic advisor for Universidad Cristiana de Logos (UCL). Evaluate and recommend the appropriate academic level and program.

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

STUDENT DATA:
Name: {student_data['applicant_name']}
Program Interest: {student_data['program_interest']}
Education Level: {student_data['education_level']}
Ministerial Experience: {student_data['ministerial_experience']}
Background: {student_data['background']}

Return ONLY valid JSON without any markdown formatting:
{{
  "recommended_level": "level here",
  "recommended_programs": ["program 1", "program 2"],
  "justification": "explanation here",
  "admissions_notes": "notes here",
  "confidence_score": 8
}}"""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        # Get response text safely
        response_text = ""
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts') and candidate.content.parts:
                response_text = candidate.content.parts[0].text
        
        if not response_text:
            raise ValueError("Empty response from Gemini")
        
        response_text = response_text.strip()
        
        # Remove markdown formatting
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        print(f"[DEBUG] Response: {response_text[:200]}")
        
        # Parse JSON
        classification = json.loads(response_text)
        
        # Validate required fields
        required = ['recommended_level', 'recommended_programs', 'justification', 'admissions_notes']
        if not all(k in classification for k in required):
            raise ValueError(f"Missing fields: {[k for k in required if k not in classification]}")
        
        print(f"[SUCCESS] Level: {classification['recommended_level']}")
        return classification
        
    except Exception as e:
        print(f"[ERROR] Classification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "recommended_level": "Certificación Básica",
            "recommended_programs": ["Certificado en Estudios Bíblicos"],
            "justification": "Error en procesamiento automático. Requiere revisión manual.",
            "admissions_notes": "⚠️ ATENCIÓN: Clasificación automática falló. Revisar manualmente.",
            "confidence_score": 1
        }