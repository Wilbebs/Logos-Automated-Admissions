
from flask import Flask, request, jsonify
import os
import json
from dotenv import load_dotenv
from flask_cors import CORS

# Import our custom modules
import form_detector  # Might be less used now but good to keep for reference
import estados_unidos
import latinoamerica
import experiencia_ministerial
import recomendacion_pastoral
import gemini_classifier
import salesforce_client
import docx_generator
import email_sender
import application_tracker
import api_routes
import machform_client

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Salesforce Client
sf_client = salesforce_client.SalesforceClient()

# Register API routes
api_routes.register_api_routes(app, sf_client)

@app.route('/', methods=['GET'])
def home():
    return "LOGOS UCL - Multi-Form Admissions System (v2.0)"

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "salesforce": "connected" if sf_client else "disconnected"
    })

def process_webhook(raw_data, form_type, form_config_module):
    print("\n" + "="*60)
    print("📨 WEBHOOK RECEIVED")
    print("="*60)
    print(f"📦 Data fields received: {len(raw_data)}")
    print(f"📄 Processing Form Type: {form_type}")

    # ENHANCED: Check ALL fields for potential file data
    print("\n🔍 DETAILED FIELD ANALYSIS:")
    print("-" * 60)
    
    for key, value in raw_data.items():
        value_str = str(value)
        
        # Check if value looks like a file path or URL
        is_file_related = (
            'file' in key.lower() or 
            'upload' in key.lower() or 
            'document' in key.lower() or
            'attach' in key.lower() or
            '.pdf' in value_str.lower() or
            '.jpg' in value_str.lower() or
            '.png' in value_str.lower() or
            '.doc' in value_str.lower() or
            '/data/' in value_str or
            'machform/data/' in value_str or
            value_str.startswith('http')
        )
        
        if is_file_related:
            value_preview = value_str[:300] + "..." if len(value_str) > 300 else value_str
            print(f"📎 {key}: {value_preview}")
    
    print("-" * 60)
    print("="*60 + "\n")

    # STEP 1: Extract Data using the specific module
    try:
        student_data = form_config_module.extract_student_data(raw_data)
        # Ensure form_name is set correctly (force overwrite with the trusted type)
        student_data['form_name'] = form_type

        # Retrieve files from MachForm DB
        entry_id = raw_data.get('EntryNumber')
        form_id = raw_data.get('FormID')

        print(f"[DEBUG] Raw data keys: {list(raw_data.keys())}")
        print(f"[DEBUG] EntryNumber: {entry_id}")
        print(f"[DEBUG] FormID: {form_id}")

        if entry_id and form_id:
            print(f"[FILES] Attempting to fetch files for entry {entry_id}, form {form_id}")
            try:
                mf_client = machform_client.MachFormClient()
                files = mf_client.get_uploaded_files(form_id, entry_id)
                
                if files:
                    print(f"[FILES] Found {len(files)} uploaded files")
                    student_data['uploaded_files'] = files
                else:
                    print(f"[FILES] No files found for this entry")
            except Exception as e:
                print(f"[FILES] Error retrieving files: {e}")
        else:
            print(f"[FILES] Skipping - EntryNumber or FormID not found in webhook data")
        
        print(f"\n🔍 STEP 1: Data Extraction")
        print(f"✓ Applicant: {student_data.get('applicant_name')}")
        print(f"✓ Email: {student_data.get('email')}")
    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

    # STEP 2: Store in Salesforce
    print("\n💾 STEP 2: Salesforce Integration")
    lead_id = None
    all_forms_complete = False
    previous_form_count = 0
    new_form_count = 0
    
    if sf_client:
        try:
            # Find or create Lead
            email = student_data.get('email', 'unknown@example.com')
            first_name = student_data.get('applicant_first_name', 'Unknown')
            last_name = student_data.get('applicant_last_name', 'Unknown')
            
            lead_id = sf_client.find_or_create_lead(email, first_name, last_name)
            
            if lead_id:
                # CHECK FOR DUPLICATES
                is_duplicate = sf_client.check_duplicate_form_type(lead_id, form_type)
                
                if is_duplicate:
                    print(f"⚠️ DUPLICATE SUBMISSION: {form_type} already exists for this Lead")
                    
                    # Send Warning Email
                    recipient = student_data.get('email')
                    if recipient:
                        print(f"[EMAIL] Sending DUPLICATE WARNING to {recipient}")
                        email_sender.send_email_with_attachment(
                            recipient=recipient,
                            student_data=student_data,
                            email_type="duplicate_warning"
                        )
                    
                    return jsonify({
                        "status": "warning",
                        "message": "Duplicate form submission detected - warning email sent",
                        "form_detected": form_type
                    }), 200

                # Create Form Submission record
                sf_client.create_form_submission(lead_id, form_type, json.dumps(raw_data, ensure_ascii=False))
                
                # Track counts BEFORE and AFTER update
                # Handle Salesforce eventual consistency: Query might not show the new record immediately
                submitted_types_list = sf_client.get_submitted_form_types(lead_id)
                
                # Ensure current form is counted even if query lags
                if form_type not in submitted_types_list:
                        submitted_types_list.append(form_type)
                
                # Deduplicate just in case
                submitted_types_set = set(submitted_types_list)
                
                new_form_count = len(submitted_types_set)
                previous_form_count = new_form_count - 1 
                
                # Update Lead form count (this puts the count in the Lead record, mostly for reference/CRM view)
                all_forms_complete = sf_client.update_lead_form_count(lead_id)
                
                print(f"✓ Salesforce records created/updated")
                print(f"✓ Form Count: {previous_form_count} -> {new_form_count}")
                print(f"✓ All forms complete: {all_forms_complete}")
            else:
                print("⚠️ Could not create/find Lead in Salesforce")
        except Exception as e:
            print(f"⚠️ Salesforce error: {e}")
    else:
        print("⚠️ Salesforce not connected - skipping")

    # STEP 3: Logic Gates (Email & Classification)
    if new_form_count < 3 and sf_client:
        # Case 1: Incomplete Application (Forms 1 or 2)
        print(f"\n📧 Sending ACKNOWLEDGMENT email ({new_form_count}/3 forms)")
        
        # Determine missing forms
        submitted_types_now = submitted_types_set if 'submitted_types_set' in locals() else set()
        
        missing_forms = []
        # Check against known form types (simplified check)
        if not any("Solicitud" in t for t in submitted_types_now):
            missing_forms.append("Solicitud Oficial de Admisión")
        if not any("Experiencia" in t for t in submitted_types_now):
            missing_forms.append("Experiencia Ministerial")
        if not any("Recomendación" in t for t in submitted_types_now):
            missing_forms.append("Recomendación Pastoral")

        email_sender.send_email_with_attachment(
            recipient=student_data.get('email'),
            student_data=student_data,
            email_type="acknowledgment",
            missing_forms=missing_forms,
            form_count=new_form_count
        )
        
        print("✅ SUCCESS - Acknowledgment sent (skipping classification)")
        return jsonify({
            "status": "success",
            "message": "Form received, acknowledgment sent",
            "progress": f"{new_form_count}/3"
        })

    elif previous_form_count < 3 and new_form_count == 3:
        # Case 2: Just Completed (Transition 2 -> 3)
        print("\n🤖 STEP 4: AI Classification (Stage 2 Triggered)")
        # Proceed to classification logic below
    else:
        # Case 3: Already complete or weird state
        if sf_client and new_form_count > 3:
                print(f"⚠️ Extra form submitted ({new_form_count}/3). Skipping re-classification.")
                return jsonify({"status": "success", "message": "Extra form received"}), 200
        print("\n🤖 STEP 4: AI Classification (Fallback/Local flow)")

    # STEP 4: Classify student
    classification_status = 'Final' if new_form_count >= 3 else 'Preliminary'
    
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
        print("[CLASSIFIER] Using Stage 1 (single-form/fallback)")
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
    print("[EMAIL] Sending FINAL recommendation email")
    
    email_sender.send_email_with_attachment(
        recipient=recipient,
        student_data=student_data,
        classification=classification,
        docx_path=docx_path,
        email_type="final"
    )
    print("✓ Email sent successfully")
    
    print("\n" + "="*60)
    print("✅ SUCCESS - Processing complete")
    print("="*60 + "\n")
    
    return jsonify({
        "status": "success",
        "form_detected": form_type,
        "applicant": student_data.get('applicant_name'),
        "email": student_data.get('email'),
        "salesforce_lead_id": lead_id,
        "all_forms_complete": all_forms_complete,
        "classification_status": classification_status,
        "report_generated": True,
        "email_sent": True
    })

def get_safe_data():
    """Helper to safely get JSON or Form data"""
    if request.is_json:
        print("📨 WEBHOOK RECEIVED (JSON format)")
        return request.get_json()
    else:
        print("📨 WEBHOOK RECEIVED (Form data format)")
        return request.form.to_dict()

# --- SPECIFIC ROUTES ---

@app.route('/webhook/estados-unidos', methods=['POST'])
def webhook_estados_unidos():
    raw_data = get_safe_data()
    return process_webhook(
        raw_data=raw_data,
        form_type="Solicitud Oficial de Admisión Estados Unidos y el Mundo",
        form_config_module=estados_unidos
    )

@app.route('/webhook/latinoamerica', methods=['POST'])
def webhook_latinoamerica():
    raw_data = get_safe_data()
    return process_webhook(
        raw_data=raw_data,
        form_type="Solicitud Oficial de Admisión Latinoamérica",
        form_config_module=latinoamerica
    )

@app.route('/webhook/experiencia', methods=['POST'])
def webhook_experiencia():
    raw_data = get_safe_data()
    return process_webhook(
        raw_data=raw_data,
        form_type="Formulario de Experiencia Ministerial",
        form_config_module=experiencia_ministerial
    )

@app.route('/webhook/recomendacion', methods=['POST'])
def webhook_recomendacion():
    raw_data = get_safe_data()
    return process_webhook(
        raw_data=raw_data,
        form_type="Formulario de Recomendación Pastoral",
        form_config_module=recomendacion_pastoral
    )

# --- DEPRECATED ROUTE ---

@app.route('/webhook/machform', methods=['POST'])
def webhook_deprecated():
    return jsonify({
      "error": "Please use form-specific endpoints",
      "endpoints": {
        "estados_unidos": "/webhook/estados-unidos",
        "latinoamerica": "/webhook/latinoamerica",
        "experiencia": "/webhook/experiencia",
        "recomendacion": "/webhook/recomendacion"
      }
    }), 400

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)