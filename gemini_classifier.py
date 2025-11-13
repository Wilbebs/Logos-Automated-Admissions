import google.generativeai as genai
import os
import json

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def classify_student(student_data):
    prompt = f"""You are an academic advisor for Universidad Cristiana de Logos (UCL). Evaluate and recommend the appropriate academic level and program.

ACADEMIC LEVELS:
1. Certificación Básica - Minimal formal education or new to theological studies
2. Pregrado - Bachelor's level (requires secondary education)
3. Postgrado - Master's level (requires undergraduate degree)
4. Doctorado - Doctoral programs (requires master's degree)

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

Return ONLY valid JSON:
{{
  "recommended_level": "string (exactly: Certificación Básica, Pregrado, Postgrado, or Doctorado)",
  "recommended_programs": ["program 1", "program 2"],
  "justification": "2-3 sentence explanation",
  "admissions_notes": "Any concerns or special considerations",
  "confidence_score": number 1-10
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
            }
        )
        
        # Handle response properly for Gemini 2.5
        try:
            # Try to access response parts directly
            response_text = response.candidates[0].content.parts[0].text.strip()
        except (AttributeError, IndexError):
            # Fallback to text attribute if available
            response_text = response.text.strip()
        
        # Clean up markdown code blocks if present
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            response_text = '\n'.join(lines).strip()
        
        classification = json.loads(response_text)
        
        required = ['recommended_level', 'recommended_programs', 'justification', 'admissions_notes']
        if not all(k in classification for k in required):
            raise ValueError("Missing required fields")
        
        return classification
        
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {
            "recommended_level": "Certificación Básica",
            "recommended_programs": ["Certificado en Estudios Bíblicos"],
            "justification": "Error en procesamiento automático. Requiere revisión manual.",
            "admissions_notes": "⚠️ ATENCIÓN: Clasificación automática falló. Revisar manualmente.",
            "confidence_score": 1
        }