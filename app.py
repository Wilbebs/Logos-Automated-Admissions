"""
LOGOS UCL - Automated Admissions System
Multi-Form Support with Two-Stage Classification + Salesforce Integration
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
from salesforce_client import SalesforceClient

app = Flask(__name__)

print("\n" + "="*50)
print("LOGOS UCL - Multi-Form Admissions System")
print("="*50)
print("✓ Form detector loaded")
print("✓ Gemini classifier loaded")
print("✓ DOCX generator loaded")
print("✓ Email sender loaded")
print("✓ Application tracker loaded")

# Initialize Salesforce client
try:
    sf_client = SalesforceClient()
    print("✓ Salesforce client loaded")
except Exception as e:
    print(f"⚠️ Salesforce initialization failed: {e}")
    sf_client = None

print("="*50 + "\n")


@app.route('/')
def home():
    """System status page"""
    return jsonify({
        "status": "running",
        "system": "LOGOS UCL Multi-Form Admissions",
        "version": "2.0",
        "salesforce_connected": sf_client is not None,
        "forms_supported": [
            "Solicitud Oficial de Admisión Estados Unidos y el Mundo",
            "Solicitud Oficial de Admisión Latinoamérica",
            "Formulario de Experiencia Ministerial",
            "Formulario de Recomendación Pastoral"
        ],
        "features": [
            "Multi-form detection",
            "Two-stage classification",
            "Salesforce integration",
            "Application tracking",
            "Automated DOCX reports",
            "Email notifications"
        ]
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "salesforce": "connected" if sf_client else "disconnected"
    })


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
        
        # STEP 2: Store in Salesforce
        print("\n💾 STEP 2: Salesforce Integration")
        lead_id = None
        all_forms_complete = False
        
        if sf_client:
            try:
                # Find or create Lead
                email = student_data.get('email', 'unknown@example.com')
                first_name = student_data.get('applicant_first_name', 'Unknown')
                last_name = student_data.get('applicant_last_name', 'Unknown')
                
                lead_id = sf_client.find_or_create_lead(email, first_name, last_name)
                
                if lead_id:
                    # Create Form Submission record
                    form_type = student_data.get('form_name', 'Unknown')
                    sf_client.create_form_submission(lead_id, form_type, json.dumps(raw_data, ensure_ascii=False))
                    
                    # Update Lead form count and check completion
                    all_forms_complete = sf_client.update_lead_form_count(lead_id)
                    
                    print(f"✓ Salesforce records created/updated")
                    print(f"✓ All forms complete: {all_forms_complete}")
                else:
                    print("⚠️ Could not create/find Lead in Salesforce")
            except Exception as e:
                print(f"⚠️ Salesforce error: {e}")
        else:
            print("⚠️ Salesforce not connected - skipping")
        
        # STEP 3: Track application (local tracking as backup)
        print("\n📊 STEP 3: Application Tracking")
        tracker = application_tracker.get_tracker()
        
        # STEP 4: Classify student
        print("\n🤖 STEP 4: AI Classification")
        
        # Determine classification stage
        classification_status = 'Final' if all_forms_complete else 'Preliminary'
        
        # If all forms complete and we have Salesforce, get comprehensive data
        if all_forms_complete and sf_client and lead_id:
            print("[CLASSIFIER] Using Stage 2 (comprehensive - all forms)")
            all_submissions = sf_client.get_all_form_submissions(lead_id)
            
            # Combine all form data for comprehensive analysis
            comprehensive_data = student_data.copy()
            comprehensive_data['all_submissions'] = all_submissions
            comprehensive_data['total_forms'] = len(all_submissions)
            
            classification = gemini_classifier.classify_student(comprehensive_data)
        else:
            print("[CLASSIFIER] Using Stage 1 (single-form)")
            classification = gemini_classifier.classify_student(student_data)
        
        print(f"✓ Level: {classification.get('recommended_level')}")
        print(f"✓ Programs: {classification.get('recommended_programs')}")
        print(f"✓ Status: {classification_status}")
        
        # STEP 5: Store Classification in Salesforce
        if sf_client and lead_id:
            print("\n💾 STEP 5: Store Classification")
            sf_client.create_classification(lead_id, classification, status=classification_status)
            print("✓ Classification saved to Salesforce")
        
        # STEP 6: Generate DOCX report
        print("\n📄 STEP 6: Generate Report")
        docx_path = docx_generator.generate_report(
            student_data=student_data,
            classification=classification
        )
        print(f"✓ Report saved: {docx_path}")
        
        # STEP 7: Send email
        print("\n📧 STEP 7: Send Email")
        
        recipient = os.getenv('RECIPIENT_EMAIL', 'web@logos.edu')
        
        # Determine email type based on completion status
        if all_forms_complete:
            print("[EMAIL] Sending FINAL recommendation email")
        else:
            print("[EMAIL] Sending acknowledgment email")
        
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
            "email": student_data.get('email'),
            "salesforce_lead_id": lead_id,
            "all_forms_complete": all_forms_complete,
            "classification_status": classification_status,
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