from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from gemini_classifier import classify_student
from docx_generator import generate_report
from email_sender import send_email_with_attachment
import traceback
from datetime import datetime

load_dotenv()
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Logos University - Automated Class Placement System",
        "version": "1.0"
    })

@app.route('/webhook/machform', methods=['POST'])
def machform_webhook():
    try:
        raw_data = request.form.to_dict() if request.form else request.json
        
        print(f"[WEBHOOK] Received submission")
        print(f"[WEBHOOK] Entry ID: {raw_data.get('entry_no', 'unknown')}")
        
        student_data = extract_student_data(raw_data)
        
        if not student_data.get('applicant_name') or not student_data.get('email'):
            return jsonify({"error": "Missing required fields"}), 400
        
        print(f"[PROCESSING] Student: {student_data['applicant_name']}")
        
        classification = classify_student(student_data)
        print(f"[GEMINI] Level: {classification['recommended_level']}")
        
        docx_path = generate_report(student_data, classification)
        print(f"[DOCX] Generated: {docx_path}")
        
        email_sent = send_email_with_attachment(
            recipient=os.getenv('RECIPIENT_EMAIL'),
            student_data=student_data,
            classification=classification,
            docx_path=docx_path
        )
        
        if os.path.exists(docx_path):
            os.remove(docx_path)
        
        print(f"[SUCCESS] Complete")
        
        return jsonify({
            "status": "success",
            "applicant": student_data['applicant_name'],
            "recommendation": {
                "level": classification['recommended_level'],
                "programs": classification['recommended_programs']
            },
            "email_sent": email_sent
        }), 200
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

def extract_student_data(raw_data):
    def get_field(element_id, default=''):
        value = raw_data.get(element_id, default)
        return value.strip() if isinstance(value, str) else str(value)
    
    title = get_field('element_1')
    first_name = get_field('element_143')
    last_name = get_field('element_6')
    full_name = f"{title} {first_name} {last_name}".strip()
    
    ministry_role = get_field('element_22', 'No especificado')
    church_name = get_field('element_87', 'No especificado')
    denomination = get_field('element_121', 'No especificado')
    years_attending = get_field('element_27', 'N/A')
    years_pastoring = get_field('element_96', 'N/A')
    church_attendance = get_field('element_102', 'N/A')
    ordained_year = get_field('element_28', 'N/A')
    ministry_summary = get_field('element_115', 'No proporcionado')
    
    high_school = get_field('element_99', 'No')
    associate = get_field('element_131', 'No')
    bachelor = get_field('element_132', 'No')
    master = get_field('element_133', 'No')
    doctoral = get_field('element_134', 'No')
    
    education_levels = []
    if doctoral != 'No': education_levels.append('Doctorado')
    if master != 'No': education_levels.append('Maestría')
    if bachelor != 'No': education_levels.append('Licenciatura')
    if associate != 'No': education_levels.append('Técnico/Associate')
    if high_school != 'No': education_levels.append('Secundaria')
    
    highest_education = education_levels[0] if education_levels else 'No especificado'
    
    ministerial_experience = f"""
Rol: {ministry_role}
Iglesia: {church_name}
Denominación: {denomination}
Años asistiendo: {years_attending}
Años pastoreando: {years_pastoring}
Asistencia dominical: {church_attendance}
Año de ordenación: {ordained_year}

Resumen: {ministry_summary}
    """.strip()
    
    has_ministry = ministry_role != 'No especificado' or church_name != 'No especificado'
    
    return {
        'submission_id': get_field('entry_no', 'N/A'),
        'applicant_name': full_name,
        'email': get_field('element_12'),
        'phone': get_field('element_11', 'No proporcionado'),
        'program_interest': get_field('element_147', 'No especificado'),
        'education_level': highest_education,
        'ministerial_experience': ministerial_experience,
        'pastoral_recommendation': 'Sí' if has_ministry else 'No proporcionado',
        'background': ministry_summary,
        'additional_notes': get_field('element_78', 'Ninguna'),
        'submitted_at': get_field('date_created', datetime.now().isoformat()),
        'desired_program': get_field('element_136', get_field('element_147')),
        'study_level_selected': get_field('element_23', 'No especificado')
    }

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)