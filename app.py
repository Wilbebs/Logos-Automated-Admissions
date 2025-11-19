"""
LOGOS UCL - Automated Admissions System
Multi-Form Support with Two-Stage Classification
"""

from flask import Flask, request, jsonify
import json
import os

# Import YOUR existing modules
import form_detector
import gemini_classifier
import docx_generator
import email_sender
import application_tracker

app = Flask(__name__)

print("\n" + "="*50)
print("LOGOS UCL - Multi-Form Admissions System")
print("="*50)
print("✓ Form detector loaded")
print("✓ Gemini classifier loaded")
print("✓ DOCX generator loaded")
print("✓ Email sender loaded")
print("✓ Application tracker loaded")
print("="*50 + "\n")


@app.route('/')
def home():
    """System status page"""
    return jsonify({
        "status": "running",
        "system": "LOGOS UCL Multi-Form Admissions",
        "version": "2.0",
        "forms_supported": [
            "Solicitud Oficial de Admisión Estados Unidos y el Mundo",
            "Solicitud Oficial de Admisión Latinoamérica",
            "Formulario de Experiencia Ministerial",
            "Formulario de Recomendación Pastoral"
        ],
        "features": [
            "Multi-form detection",
            "Two-stage classification",
            "Application tracking",
            "Automated DOCX reports",
            "Email notifications"
        ]
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})


@app.route('/webhook/machform', methods=['POST'])
def webhook():
    """
    Main webhook endpoint - handles ALL forms
    """
    print("\n" + "="*60)
    print("📨 WEBHOOK RECEIVED")
    print("="*60)
    
    try:
        # Get raw data
        raw_data = request.get_json() or request.form.to_dict()
        
        if not raw_data:
            print("❌ No data received")
            return jsonify({"error": "No data"}), 400
        
        print(f"📦 Data fields received: {len(raw_data)}")
        
        # STEP 1: Detect which form was submitted
        print("\n🔍 STEP 1: Form Detection")
        student_data = form_detector.extract_student_data(raw_data)
        
        if not student_data or student_data.get('form_id') == 'unknown':
            print("⚠️ Could not identify form")
            return jsonify({
                "status": "warning",
                "message": "Form could not be identified",
                "received_fields": list(raw_data.keys())[:10]
            }), 200
        
        print(f"✓ Detected: {student_data.get('form_name')}")
        print(f"✓ Applicant: {student_data.get('applicant_name')}")
        print(f"✓ Email: {student_data.get('email')}")
        
        # STEP 2: Track application
        print("\n📊 STEP 2: Application Tracking")
        tracker = application_tracker.get_tracker()
        
        # This is where we'd track the submission
        # For now, just check if it's the main application form
        is_main_form = student_data.get('form_id') in ['estados_unidos_mundo', 'latinoamerica']
        
        # STEP 3: Classify student (using YOUR gemini_classifier.py)
        print("\n🤖 STEP 3: AI Classification")
        classification = gemini_classifier.classify_student(student_data)
        
        print(f"✓ Level: {classification.get('recommended_level')}")
        print(f"✓ Programs: {classification.get('recommended_programs')}")
        
        # STEP 4: Generate DOCX report (FIXED FUNCTION NAME)
        print("\n📄 STEP 4: Generate Report")
        docx_path = docx_generator.generate_report(
            student_data=student_data,
            classification=classification
        )
        print(f"✓ Report saved: {docx_path}")
        
        # STEP 5: Send email (FIXED FUNCTION NAME)
        print("\n📧 STEP 5: Send Email")
        
        recipient = os.getenv('RECIPIENT_EMAIL', 'web@logos.edu')
        
        email_sender.send_email_with_attachment(
            recipient=recipient,
            student_data=student_data,
            classification=classification,
            docx_path=docx_path
        )
        print("✓ Email sent successfully")
        
        print("\n" + "="*60)
        print("✅ SUCCESS - Processing complete")
        print("="*60 + "\n")
        
        return jsonify({
            "status": "success",
            "form_detected": student_data.get('form_name'),
            "applicant": student_data.get('applicant_name'),
            "classification": classification,
            "report_generated": True,
            "email_sent": True
        })
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)