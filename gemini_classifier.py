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
Pastoral Recommendation: {student_data['pastoral_recommendation']}
Background: {student_data['background']}
Notes: {student_data['additional_notes']}

CRITICAL: Return ONLY valid JSON. Use double quotes for strings. Do not include markdown code blocks. Do not use single quotes inside strings.

{{
  "recommended_level": "Certificación Básica",
  "recommended_programs": ["Program 1", "Program 2"],
  "justification": "Brief explanation without quotes or special characters",
  "admissions_notes": "Any concerns without quotes or special characters",
  "confidence_score": 10
}}"""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.3,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 1024,
                'response_mime_type': 'application/json',
            }
        )
        
        # Access response parts directly
        response_text = response.candidates[0].content.parts[0].text.strip()
        
        # Clean up any markdown remnants
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        # Debug output
        print(f"[DEBUG] Gemini response length: {len(response_text)}")
        print(f"[DEBUG] First 500 chars: {response_text[:500]}")
        
        classification = json.loads(response_text)
        
        required = ['recommended_level', 'recommended_programs', 'justification', 'admissions_notes']
        if not all(k in classification for k in required):
            raise ValueError("Missing required fields")
        
        print(f"[SUCCESS] Classification: {classification['recommended_level']}")
        return classification
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON Parse Error: {e}")
        print(f"[ERROR] Full response: {response_text if 'response_text' in locals() else 'No response'}")
        return {
            "recommended_level": "Certificación Básica",
            "recommended_programs": ["Certificado en Estudios Bíblicos"],
            "justification": "Error en procesamiento de respuesta JSON. Requiere revisión manual.",
            "admissions_notes": "⚠️ ATENCIÓN: Error parseando respuesta de IA. Revisar manualmente.",
            "confidence_score": 1
        }
    except Exception as e:
        print(f"[ERROR] Gemini Error: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            "recommended_level": "Certificación Básica",
            "recommended_programs": ["Certificado en Estudios Bíblicos"],
            "justification": "Error en procesamiento automático. Requiere revisión manual.",
            "admissions_notes": "⚠️ ATENCIÓN: Clasificación automática falló. Revisar manualmente.",
            "confidence_score": 1
        }