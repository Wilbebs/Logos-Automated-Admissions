import resend
import os

def send_email_with_attachment(recipient, student_data, classification=None, docx_path=None, email_type="final", missing_forms=None, form_count=0):
    # Debug: print all environment variables that start with RESEND or GEMINI
    print("[DEBUG] Environment variables:")
    for key in os.environ:
        if 'RESEND' in key or 'GEMINI' in key or 'GMAIL' in key or 'RECIPIENT' in key:
            value = os.environ[key]
            print(f"  {key} = {value[:15]}..." if len(value) > 15 else f"  {key} = {value}")
    
    api_key = os.getenv('RESEND_API_KEY')
    
    if not api_key:
        print("[EMAIL] Missing Resend API key - skipping email")
        print(f"[EMAIL] Checked for: RESEND_API_KEY")
        return False
    
    print(f"[EMAIL] API key found: {api_key[:10]}...")
    
    resend.api_key = api_key
    
    # Use Resend's test domain
    sender_email = "onboarding@resend.dev"
    
    # --- BUILD EMAIL CONTENT BASED ON TYPE ---
    if email_type == "acknowledgment":
        # EMAIL TYPE 1: Acknowledgment (Forms 1 & 2)
        subject = f"Formulario Recibido - Pasos Siguientes ({form_count}/3)"
        
        # Build missing forms list
        missing_list_html = ""
        if missing_forms:
            missing_list_html = "<ul>" + "".join([f"<li>{form}</li>" for form in missing_forms]) + "</ul>"
        else:
            missing_list_html = "<p>Ninguno.</p>"
            
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #0066cc;">Formulario Recibido: {student_data.get('form_name', 'Formulario')}</h2>
            
            <p>Estimado/a <strong>{student_data['applicant_name']}</strong>,</p>
            
            <p>Hemos recibido su formulario correctamente.</p>
            
            <p><strong>Progreso de su solicitud:</strong> {form_count} de 3 formularios recibidos.</p>
            
            <h3 style="color: #cc6600;">Documentos pendientes para completar su solicitud:</h3>
            {missing_list_html}
            
            <p>Una vez que recibamos los 3 formularios requeridos, nuestro sistema procesará su solicitud completa y le enviará la clasificación académica oficial.</p>
            
            <hr>
            <p style="font-size: 12px; color: #666;">
              Oficina de Admisiones - Universidad Cristiana de Logos
            </p>
          </body>
        </html>
        """
        attachments = []
        print(f"[EMAIL] Prepared ACKNOWLEDGMENT email for {recipient}")
        
    else:
        # EMAIL TYPE 2: Final Classification (Form 3)
        subject = f"Clasificación Académica Completa: {student_data['applicant_name']}"
        
        program_list_html = ""
        if classification and 'recommended_programs' in classification:
            program_list_html = "<ul>" + "".join([f"<li>{p}</li>" for p in classification['recommended_programs']]) + "</ul>"
            
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #0066cc;">Nueva Solicitud Clasificada</h2>
            
            <p><strong>Solicitante:</strong> {student_data['applicant_name']}</p>
            <p><strong>Correo:</strong> {student_data.get('email', 'No proporcionado')}</p>
            
            <h3 style="color: #0066cc;">Recomendación:</h3>
            <p><strong>Nivel:</strong> <span style="color: #0066cc; font-size: 16px;">{classification.get('recommended_level', 'N/A') if classification else 'N/A'}</span></p>
            <p><strong>Programas:</strong></p>
            {program_list_html}
            
            <p><strong>Justificación:</strong><br>{classification.get('justification', 'N/A') if classification else 'N/A'}</p>
            
            <hr>
            
            <p style="font-size: 12px; color: #666;">
              Revise el documento adjunto para más detalles.<br>
              Sistema de Clasificación Académica - UCL
            </p>
          </body>
        </html>
        """
        
        attachments = []
        if docx_path:
            try:
                with open(docx_path, 'rb') as f:
                    file_content = f.read()
                
                attachments = [{
                    "filename": os.path.basename(docx_path),
                    "content": list(file_content),
                }]
            except Exception as e:
                print(f"[EMAIL] Error loading attachment: {e}")
        
        print(f"[EMAIL] Prepared FINAL email for {recipient}")

    try:
        print(f"[EMAIL] Sending via Resend to {recipient}...")
        
        params = {
            "from": f"UCL Admissions <{sender_email}>",
            "to": [recipient],
            "subject": subject,
            "html": html_body,
            "attachments": attachments
        }
        
        response = resend.Emails.send(params)
        print(f"[EMAIL] ✓ Successfully sent! ID: {response['id']}")
        return True
        
    except Exception as e:
        print(f"[EMAIL] ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False