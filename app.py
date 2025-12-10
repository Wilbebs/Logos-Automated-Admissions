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
                    form_type = student_data.get('form_name', 'Unknown')
                    is_duplicate = sf_client.check_duplicate_form_type(lead_id, form_type)
                    
                    if is_duplicate:
                        print(f"⚠️ DUPLICATE SUBMISSION: {form_type} already exists for this Lead")
                        return jsonify({
                            "status": "warning",
                            "message": "Duplicate form submission detected - ignoring",
                            "form_detected": form_type
                        }), 200

                    # Create Form Submission record
                    sf_client.create_form_submission(lead_id, form_type, json.dumps(raw_data, ensure_ascii=False))
                    
                    # Track counts BEFORE and AFTER update
                    # We need to query current count first? update_lead_form_count updates it...
                    # Let's trust update_lead_form_count logic, but we need the actual count
                    # To do this reliably, we can get count from submitted types
                    submitted_types = sf_client.get_submitted_form_types(lead_id)
                    new_form_count = len(submitted_types)
                    previous_form_count = new_form_count - 1 # Since we just added one
                    
                    # Update Lead form count
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
        
        # STEP 3: Track application (local tracking as backup)
        print("\n📊 STEP 3: Application Tracking")
        tracker = application_tracker.get_tracker()
        
        # LOGIC GATES FOR CLASSIFICATION
        if new_form_count < 3 and sf_client:
            # Case 1: Incomplete Application (Forms 1 or 2)
            print(f"\n📧 Sending ACKNOWLEDGMENT email ({new_form_count}/3 forms)")
            
            # Determine missing forms
            submitted_types = sf_client.get_submitted_form_types(lead_id)
            required_forms = [
                "Solicitud Oficial de Admisión Estados Unidos y el Mundo", # Or Latinoamerica
                "Formulario de Experiencia Ministerial",
                "Formulario de Recomendación Pastoral"
            ]
            # Simplistic matching for display
            missing_forms = []
            if not any("Solicitud" in t for t in submitted_types):
                missing_forms.append("Solicitud Oficial de Admisión")
            if not any("Experiencia" in t for t in submitted_types):
                missing_forms.append("Experiencia Ministerial")
            if not any("Recomendación" in t for t in submitted_types):
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
            
            # Continue to existing classification logic...
            pass # Fall through to below code
            
        else:
            # Case 3: Already complete (Re-trigger? Or >3 forms?)
            # Or if Salesforce usage skipped
            if sf_client and new_form_count > 3:
                 print(f"⚠️ Extra form submitted ({new_form_count}/3). Skipping re-classification.")
                 return jsonify({"status": "success", "message": "Extra form received"}), 200
            
            # Fallback for local testing/no-salesforce
            print("\n🤖 STEP 4: AI Classification (Fallback/Local flow)")

        # STEP 4: Classify student
        
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