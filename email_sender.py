import resend
import os

def send_email_with_attachment(recipient, student_data, classification, docx_path):
    api_key = os.getenv('RESEND_API_KEY')
    sender_email = os.getenv('GMAIL_USER', 'admissions@yourdomain.com')
    
    if not api_key:
        print("[EMAIL] Missing Resend API key - skipping email")
        return False
    
    resend.api_key = api_key
    
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
        
        print("[EMAIL] Sending via Resend...")
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
        
        email = resend.Emails.send(params)
        print(f"[EMAIL] Successfully sent to {recipient} (ID: {email['id']})")
        return True
        
    except Exception as e:
        print(f"[EMAIL] Error sending via Resend: {e}")
        return False