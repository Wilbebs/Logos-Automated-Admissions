import resend
import os

def send_email_with_attachment(recipient, student_data, classification, docx_path):
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
    
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #0066cc;">Nueva Solicitud Clasificada</h2>
        
        <p><strong>Solicitante:</strong> {student_data['applicant_name']}</p>
        <p><strong>Correo:</strong> {student_data['email']}</p>
        
        <h3 style="color: #0066cc;">Recomendación:</h3>
        <p><strong>Nivel:</strong> <span style="color: #0066cc; font-size: 16px;">{classification['recommended_level']}</span></p>
        <p><strong>Programas:</strong></p>
        <ul>
          {''.join([f"<li>{p}</li>" for p in classification['recommended_programs']])}
        </ul>
        
        <p><strong>Justificación:</strong><br>{classification['justification']}</p>
        
        <hr>
        
        <p style="font-size: 12px; color: #666;">
          Revise el documento adjunto para más detalles.<br>
          Sistema de Clasificación Académica - UCL
        </p>
      </body>
    </html>
    """
    
    try:
        with open(docx_path, 'rb') as f:
            file_content = f.read()
        
        print(f"[EMAIL] Sending via Resend to {recipient}...")
        
        params = {
            "from": f"UCL Admissions <{sender_email}>",
            "to": [recipient],
            "subject": f"Nueva Clasificación Académica: {student_data['applicant_name']}",
            "html": html_body,
            "attachments": [
                {
                    "filename": os.path.basename(docx_path),
                    "content": list(file_content),
                }
            ],
        }
        
        response = resend.Emails.send(params)
        print(f"[EMAIL] ✓ Successfully sent! ID: {response['id']}")
        return True
        
    except Exception as e:
        print(f"[EMAIL] ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False