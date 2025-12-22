"""
Enhanced Multi-Form Classifier
Combines data from multiple forms for comprehensive classification
"""

import vertexai
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import os
import json
from google.oauth2 import service_account
from typing import Dict, List, Optional
from application_tracker import get_tracker, ApplicationStatus
import base64
from pathlib import Path

def process_file_for_gemini(file_path):
    """Convert file to format Gemini can process"""
    try:
        ext = Path(file_path).suffix.lower()
        # Gemini-supported MIME types only
        mime_types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        
        mime_type = mime_types.get(ext)
        
        if not mime_type:
            print(f"[CLASSIFIER] Skipping unsupported file type for Gemini: {os.path.basename(file_path)}")
            return None
        
        # Read file
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Convert to base64
        file_b64 = base64.b64encode(file_data).decode('utf-8')
        
        return {
            'mime_type': mime_type,
            'data': file_b64,
            'filename': os.path.basename(file_path)
        }
        
    except Exception as e:
        print(f"[CLASSIFIER] Error reading file {file_path}: {e}")
        return None


class MultiFormClassifier:
    """
    Enhanced classifier that can work with:
    1. Single form (initial classification)
    2. Multiple forms (final comprehensive classification)
    """
    
    def __init__(self):
        # Initialize Vertex AI with project credentials
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'gen-lang-client-0586026725')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        print(f"[CLASSIFIER] Initializing Vertex AI: {project_id} / {location}")
        
        # Load credentials from environment variable
        credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        
        if credentials_json:
            # Parse JSON and create credentials object
            try:
                credentials_info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                vertexai.init(project=project_id, location=location, credentials=credentials)
                print("[CLASSIFIER] Using service account credentials")
            except Exception as e:
                print(f"[CLASSIFIER] Error loading service account credentials: {e}")
                vertexai.init(project=project_id, location=location)
        else:
            # Fallback to default credentials (for local development)
            vertexai.init(project=project_id, location=location)
            print("[CLASSIFIER] Using default credentials")
        
        # Use Gemini 1.5 Flash via Vertex AI
        self.model = GenerativeModel('gemini-2.5-flash')
        self.tracker = get_tracker()
    
    def classify_single_form(self, student_data: Dict) -> Dict:
        """
        Initial classification based on a single form (Solicitud Oficial).
        This is the STAGE 1 classification - preliminary assessment.
        """
        prompt = self._build_single_form_prompt(student_data)
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            classification = json.loads(response_text)
            classification['classification_type'] = 'preliminary'
            classification['stage'] = 1
            
            print(f"[CLASSIFIER] Stage 1 - Preliminary: {classification['recommended_level']}")
            return classification
            
        except Exception as e:
            print(f"[CLASSIFIER] Stage 1 failed: {str(e)}")
            return self._get_fallback_classification()
    
    def classify_multi_form(self, email: str, student_data: Dict, all_submissions: List = None) -> Dict:
        """
        Final classification based on ALL submitted forms.
        This is the STAGE 2 classification - comprehensive assessment.
        
        Args:
            email: Applicant email
            student_data: Basic student data
            all_submissions: Optional list of Salesforce Form_Submission objects
        """
        # Option A: Use Salesforce data (Preferred)
        if all_submissions and len(all_submissions) >= 3:
            print(f"[CLASSIFIER] Using Stage 2 (comprehensive - {len(all_submissions)} forms from Salesforce)")
            
            # Create a temporary app context structure from Salesforce data
            # This avoids rewriting the prompt builder
            parsed_submissions = []
            for sub in all_submissions:
                try:
                    # Parse the JSON string back to dict
                    form_data = json.loads(sub.get('Form_Data_JSON__c', '{}'))
                    
                    parsed_submissions.append({
                        'form_type': sub.get('Form_Type__c'),
                        'form_name': sub.get('Form_Type__c'),
                        'submitted_at': sub.get('Submission_Date__c'),
                        'data_snapshot': {
                            'program_interest': form_data.get('element_3', 'N/A'), # Example mappings
                            'education_level': form_data.get('element_4', 'N/A'),
                            'raw_data': form_data
                        }
                    })
                except Exception as e:
                    print(f"[CLASSIFIER] Error parsing submission: {e}")

            # Mock an app object structure for the prompt builder
            class MockApp:
                def __init__(self):
                    self.forms_submitted = []
                    self.created_at = "N/A"
                    self.updated_at = "N/A"
                    self.status = "Complete"
                    self.required_forms = ["Solicitud Oficial", "Experiencia Ministerial", "Recomendación Pastoral"]

            app = MockApp()
            # Add simple objects that behave like FormSubmission
            for ps in parsed_submissions:
                class MockSubmission:
                    def __init__(self, data):
                        self.form_type = data['form_type']
                        self.form_name = data['form_name']
                        self.submitted_at = data['submitted_at']
                        self.data_snapshot = data['data_snapshot']['raw_data'] # Use full data
                
                app.forms_submitted.append(MockSubmission(ps))
                
        # Option B: Fallback to local tracker
        else:
            print("[CLASSIFIER] Salesforce data missing/incomplete - falling back to local tracker")
            app = self.tracker.get_application(email)
            
            if not app or not self.tracker.is_application_complete(email):
                print("[CLASSIFIER] Cannot do Stage 2 - application incomplete")
                return self.classify_single_form(student_data)
        
        # Build enriched prompt with ALL form data
        prompt = self._build_multi_form_prompt(app, student_data)
        
        try:
            # Build message content with files
            # NOTE: When documents are included, everything in the list must be a Part object
            message_content = [Part.from_text(prompt)]

            # Add uploaded documents if available
            if student_data.get('uploaded_documents'):
                for doc in student_data['uploaded_documents']:
                    # Use Part object for multimodal input
                    message_content.append(
                        Part.from_data(
                            data=base64.b64decode(doc['data']),
                            mime_type=doc['mime_type']
                        )
                    )
                print(f"[CLASSIFIER] Including {len(student_data['uploaded_documents'])} documents in analysis")

            # Then call Gemini with message_content instead of just prompt_text
            response = self.model.generate_content(message_content)
            response_text = response.text
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
        prompt = f"""You are an academic advisor for Universidad Cristiana de Logos (UCL). Perform a COMPREHENSIVE evaluation based on ALL submitted forms and documents.

## Official UCL Admission Requirements

### Certificación Básica
Required Documents:
- Inscripción al programa
- Recomendación pastoral
- Pago de activación
NOTE: NO requiere High School diploma

### Pregrado (Licenciatura)
Required Documents:
- Formulario admisión (USA/Latinoamérica)
- Formulario experiencia ministerial
- Recomendación pastoral
- PDF título High School/técnico/profesional
- Transcripción estudios ministeriales previos (si aplica)
- Pago: $60 USD (USA) / $40 USD (Latinoamérica)

### Postgrado - Maestría
Required Documents:
- Formulario admisión (USA/Latinoamérica)
- Formulario experiencia ministerial
- Recomendación pastoral
- PDF título High School
- **PDF y transcripción oficial de LICENCIATURA MINISTERIAL**
- Pago: $60 USD (USA) / $40 USD (Latinoamérica)

CRITICAL: Requires MINISTERIAL bachelor's degree (theology/ministry).
Secular bachelor's alone is NOT sufficient.

### Postgrado - Doctorado
Required Documents:
- Formulario admisión (USA/Latinoamérica)
- Formulario experiencia ministerial
- Recomendación pastoral
- PDF título High School
- **PDF y transcripción oficial de MAESTRÍA MINISTERIAL**
- Pago: $60 USD (USA) / $40 USD (Latinoamérica)

CRITICAL: Requires MINISTERIAL master's degree (M.Div, M.Th).
Secular master's alone is NOT sufficient.

## CRITICAL RULE: Ministerial vs Secular Education

For POSTGRADO (Maestría/Doctorado):
- Ministerial degrees = Theology, Ministry, Pastoral Studies, Biblical Studies
- Secular degrees = Engineering, Business, Medicine, etc.

DECISION RULES:
✅ Licenciatura en Teología + transcript → Qualifies for Maestría
✅ Bachelor of Ministry + transcript → Qualifies for Maestría
❌ Ingeniero + 20 years pastor → Does NOT qualify for Maestría (needs ministerial bachelor's)
❌ MBA + Bible certificate → Does NOT qualify for Maestría (needs ministerial bachelor's)

If applicant has ONLY secular degree:
→ Recommend: "Complete Licenciatura en Teología first, then advance to Maestría"
→ Explain pathway: "Many of our Maestría students started with secular degrees and completed ministerial training first. This ensures strong theological foundation."

## Ministry Experience Consideration

PREGRADO Level:
✅ 4+ years as pastor/teacher CAN compensate for missing bachelor's degree
✅ Strong ministry + pastoral recommendation = qualified for Pregrado
Example: No bachelor's + 6 years youth pastor + strong recommendation → Pregrado ✅

POSTGRADO Level:
❌ Ministry experience CANNOT substitute for missing degrees
❌ 20 years as pastor + no bachelor's → Still needs Pregrado first
✅ Ministry experience ENHANCES application but doesn't replace education requirements

Decision Framework:
- Has ministerial bachelor's + 5 years ministry → Maestría ✅
- Has secular bachelor's + 15 years ministry → Pregrado in ministry first
- No bachelor's + 20 years ministry → Pregrado (experience helps but can't skip)

## Pastoral Recommendation Validation

ACCEPTABLE Recommenders:
✅ Pastor principal
✅ Co-pastor
✅ Tesorero (Church Treasurer)
✅ Anciano de la iglesia (Church Elder)

NOT ACCEPTABLE:
❌ Cónyuge (Spouse)
❌ Familiar directo (Family member)
❌ Miembro regular sin liderazgo

QUALITY INDICATORS:
Strong Recommendation:
- Knows applicant 2+ years
- Specific examples of ministry service
- Describes spiritual gifts and character
- No reservations or qualifications

Weak Recommendation:
- Superficial knowledge of applicant
- Generic language ("es buena persona")
- Very brief (less than 3 sentences)
- Includes warnings ("sin embargo...", "pero a veces...")

ACTION: If recommendation is from spouse/family → FLAG for manual review
ACTION: If recommendation is weak/generic → Note in confidence score

## Document Verification Requirement

BEFORE classifying, CHECK:
1. Are all 3 forms submitted?
2. Are required documents for target level provided?
3. Are TRANSCRIPTS provided or just claims?

CLASSIFICATION RULES:
- All documents verified → High confidence (85-100%)
- Some documents, verbal claims → Medium confidence (60-84%)
- Missing critical documents → Low confidence (<60%)
- No document verification → PENDING classification

When documents are MISSING:
→ Output: "PENDING DOCUMENT VERIFICATION"
→ Provide: Conditional recommendation ("IF you provide X, you qualify for Y")
→ List: Specific missing documents

## Handling Over-Aspiring Applicants

When applicant selects level too high for credentials:
CORRECT APPROACH ✅:
"Your ministry experience is impressive and demonstrates strong ministry calling. To reach your desired level, we recommend this pathway:
STEP 1: Complete the appropriate preparatory level (duration varies)
STEP 2: Continue building ministry experience
STEP 3: Advance to your target level
Many of our successful students followed this path and are now thriving in advanced ministry roles."

## Required Output Format

IMPORTANT: Provide 2-3 program options when qualified, not just one.

Return ONLY valid JSON without any markdown formatting:
{{
  "recommended_level": "level here",
  "recommended_programs": ["program 1", "program 2"],
  "program_explanations": {{
    "program 1": "explanation here",
    "program 2": "explanation here"
  }},
  "confidence_score": 90,
  "reasoning": {{
    "educational_assessment": "assessment of academic credentials",
    "ministry_experience_assessment": "assessment of ministry background",
    "pastoral_recommendation_assessment": "assessment of recommendation quality",
    "documents_missing": ["doc1", "doc2"],
    "pathway_explanation": "explanation for over-aspiring applicants (if applicable)"
  }},
  "next_steps": ["step 1", "step 2"],
  "admissions_notes": "Internal notes for committee"
}}

---
## COMPREHENSIVE STUDENT DATA (from ALL forms):

FROM SOLICITUD OFICIAL:
Name: {student_data.get('applicant_name', 'Unknown')}
Email: {student_data.get('email', 'Unknown')}
Program Interest: {student_data.get('program_interest', 'N/A')}
Self-Reported Education: {student_data.get('education_level', 'N/A')}
Study Level Selected: {student_data.get('study_level_selected', 'N/A')}
Basic Ministry Info: {student_data.get('ministerial_experience', 'N/A')}

FORMS SUBMITTED:
{json.dumps(forms_data, indent=2, ensure_ascii=False)}

APPLICATION STATUS:
- Created: {app.created_at}
- Updated: {app.updated_at}
- Forms Submitted: {len(app.forms_submitted)}/{len(app.required_forms)}
- Status: {app.status}

---
## Learn From These Classification Examples

### Example 1: Clear Maestría Case ✅
Input:
- Education: Licenciatura en Teología (2020, UCL) + transcript provided
- Ministry: Pastor asociado 6 años
- Recommendation: Strong from senior pastor
- Documents: All required documents attached

Output:
{{
  "recommended_level": "Postgrado - Maestría",
  "recommended_programs": [
    "Maestría en Divinidad (M.Div)",
    "Maestría en Liderazgo Ministerial"
  ],
  "program_explanations": {{
    "Maestría en Divinidad (M.Div)": "Programa integral para el ministerio pastoral a tiempo completo.",
    "Maestría en Liderazgo Ministerial": "Enfoque en desarrollo organizacional y liderazgo de equipos."
  }},
  "confidence_score": 92,
  "reasoning": {{
    "educational_assessment": "Verified ministerial bachelor's with official transcript.",
    "ministry_experience_assessment": "6 years as associate pastor, substantial leadership.",
    "pastoral_recommendation_assessment": "Strong verified recommendation from senior pastor.",
    "documents_missing": []
  }},
  "next_steps": ["Enrollment fee payment", "Course selection"]
}}

---

### Example 2: Over-Aspiring (Secular Degree) ⚠️
Input:
- Education: Ingeniero Civil + 15 years as senior pastor
- Ministry: Senior pastor 15 años
- Goal: Maestría en Teología
- Documents: Engineering degree only

Output:
{{
  "recommended_level": "Pregrado - Licenciatura en Teología",
  "recommended_programs": [
    "Licenciatura en Teología",
    "Licenciatura en Ministerio Pastoral"
  ],
  "program_explanations": {{
    "Licenciatura en Teología": "Enfoque académico, ideal para futuros profesores.",
    "Licenciatura en Ministerio Pastoral": "Enfoque práctico, preparación pastoral."
  }},
  "confidence_score": 78,
  "reasoning": {{
    "educational_assessment": "Secular bachelor's degree (Engineering) does not meet ministerial education requirement for Maestría. Must complete ministerial bachelor's first.",
    "ministry_experience_assessment": "Exceptional 15 years as senior pastor - excellent preparation.",
    "pastoral_recommendation_assessment": "Standard pastoral recommendation.",
    "pathway_explanation": "Your ministry experience is outstanding. Complete Licenciatura en Teología (4 years, may accelerate with prior learning credit) → Advance to Maestría. This pathway ensures strong theological foundation for graduate studies.",
    "documents_missing": []
  }},
  "next_steps": [
    "Enroll in Licenciatura en Teología",
    "Request evaluation of ministry experience for possible credit",
    "Plan to advance to Maestría upon completion"
  ]
}}

---

### Example 3: Missing Documents (Pending) 📋
Input:
- Claims: "Tengo maestría en teología"
- Ministry: 8 years pastor
- Documents: Forms only, NO transcripts

Output:
{{
  "recommended_level": "PENDING DOCUMENT VERIFICATION",
  "recommended_programs": [],
  "confidence_score": 30,
  "reasoning": {{
    "educational_assessment": "Applicant claims master's degree but NO official documents provided. Cannot verify education level.",
    "ministry_experience_assessment": "8 years of pastoral experience claimed.",
    "pastoral_recommendation_assessment": "Pending review.",
    "documents_missing": [
      "PDF de título de maestría",
      "Transcripción oficial de maestría",
      "PDF de título de licenciatura",
      "Transcripción oficial de licenciatura"
    ]
  }},
  "admissions_notes": "CRITICAL: Cannot proceed without document verification.",
  "next_steps": [
    "URGENT: Submit official transcript from master's program",
    "Submit official transcript from bachelor's program",
    "Once received, final classification will be provided"
  ]
}}

---

### Example 4: Certificación (No High School) ✅
Input:
- Education: Primaria completa (elementary only)
- Ministry: Miembro iglesia 1 año
- Goal: "Aprender la Biblia"

Output:
{{
  "recommended_level": "Certificación Básica",
  "recommended_programs": [
    "Certificado en Estudios Bíblicos"
  ],
  "program_explanations": {{
    "Certificado en Estudios Bíblicos": "Proporciona una base sistemática para el estudio de la Biblia."
  }},
  "confidence_score": 90,
  "reasoning": {{
    "educational_assessment": "No formal secondary education. Certificación programs are open access - no prerequisites required.",
    "ministry_experience_assessment": "New believer seeking foundation - perfect for certificación.",
    "pastoral_recommendation_assessment": "Simple membership confirmation.",
    "documents_missing": []
  }},
  "next_steps": [
    "Register for Certificado en Estudios Bíblicos",
    "Complete pastoral recommendation form",
    "Submit activation payment"
  ]
}}

---

### Example 5: Pregrado with Ministry Substitution ✅
Input:
- Education: High School only (no bachelor's)
- Ministry: Pastor de jóvenes 6 años, detailed description
- Recommendation: Exceptional from senior pastor with specific examples
- Documents: High school diploma + ministry portfolio

Output:
{{
  "recommended_level": "Pregrado - Licenciatura",
  "recommended_programs": [
    "Licenciatura en Ministerio Pastoral",
    "Licenciatura en Educación Cristiana"
  ],
  "program_explanations": {{
    "Licenciatura en Ministerio Pastoral": "Preparación práctica para el liderazgo de iglesia.",
    "Licenciatura en Educación Cristiana": "Enfoque en enseñanza y formación espiritual."
  }},
  "confidence_score": 85,
  "reasoning": {{
    "educational_assessment": "Has high school diploma. No bachelor's degree, but ministry experience qualifies for Pregrado.",
    "ministry_experience_assessment": "6 years as youth pastor with clear responsibilities (40+ students, organized retreats, led discipleship). Meets ministry experience threshold for Pregrado consideration.",
    "pastoral_recommendation_assessment": "Exceptional recommendation with specific examples of teaching gifts and leadership.",
    "documents_missing": []
  }},
  "next_steps": [
    "Enroll in Licenciatura en Ministerio Pastoral",
    "Request evaluation of ministry experience for possible course credit",
    "Submit all required documents and admission payment"
  ]
}}

THESE EXAMPLES SHOW THE EXPECTED DEPTH AND FORMAT OF YOUR CLASSIFICATIONS.
"""
        
        return prompt
    

    
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

    # NEW: Fetch files from MachForm if we have email
    if email:
        try:
            from machform_client import MachFormClient
            mf = MachFormClient()
            
            # Query MachForm for entries by this email
            files = mf.get_files_by_email(email)
            
            if files:
                print(f"[CLASSIFIER] Found {len(files)} uploaded files")
                print(f"[CLASSIFIER] Attempting to download files...")
                
                # Group by entry
                entries = {}
                for file_info in files[:10]:
                    form_id = file_info.get('form_id')
                    entry_id = file_info.get('entry_id')
                    
                    print(f"[CLASSIFIER] File: form={form_id}, entry={entry_id}")
                    
                    if not entry_id:
                        print(f"[CLASSIFIER] Skipping file - no entry_id")
                        continue
                        
                    key = (form_id, entry_id)
                    if key not in entries:
                        entries[key] = []
                    entries[key].append(file_info)
                
                print(f"[CLASSIFIER] Grouped into {len(entries)} entries")
                
                downloaded_files = []
                for (form_id, entry_id), file_list in entries.items():
                    print(f"[CLASSIFIER] Processing entry: form={form_id}, entry={entry_id}")
                    
                    links = mf.get_download_links_from_entry(form_id, entry_id)
                    
                    for link in links:
                        local_path = mf.download_file_from_link(link['url'], link['filename'])
                        if local_path:
                            downloaded_files.append(local_path)
                
                print(f"[CLASSIFIER] Total files downloaded: {len(downloaded_files)}")
                
                if downloaded_files:
                    print(f"[CLASSIFIER] Successfully downloaded {len(downloaded_files)} files")
                    
                    # Process files for Gemini
                    file_parts = []
                    for file_path in downloaded_files[:5]:  # Limit to 5 files to avoid token limits
                        try:
                            file_part = process_file_for_gemini(file_path)
                            if file_part:
                                file_parts.append(file_part)
                                print(f"[CLASSIFIER] Processed file: {os.path.basename(file_path)[:40]}")
                        except Exception as e:
                            print(f"[CLASSIFIER] Error processing file {file_path}: {e}")
                    
                    if file_parts:
                        print(f"[CLASSIFIER] Sending {len(file_parts)} files to Gemini")
                        # Add files to the prompt
                        student_data['uploaded_documents'] = file_parts
                    else:
                        print(f"[CLASSIFIER] No files successfully processed for Gemini")
                    
                # Attach to student_data for potential use in prompts or downstream
                student_data['uploaded_files'] = files
        except Exception as e:
            print(f"[CLASSIFIER] Could not retrieve files: {e}")
    
    # Priority 1: Use direct Salesforce data if available
    if 'all_submissions' in student_data:
         # all_submissions field is injected by app.py when it detects completion
         return classifier.classify_multi_form(email, student_data, student_data['all_submissions'])
    
    # Priority 2: Check local tracker
    if email:
        tracker = get_tracker()
        if tracker.is_application_complete(email):
            print("[CLASSIFIER] Application complete (local) - using Stage 2")
            return classifier.classify_multi_form(email, student_data)
    
    # Default: Stage 1 (single form)
    print("[CLASSIFIER] Using Stage 1 (single-form) classification")
    return classifier.classify_single_form(student_data)