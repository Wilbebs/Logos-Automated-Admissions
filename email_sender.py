import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

def send_email_with_attachment(recipient, student_data, classification, docx_path):
    sender_email = os.getenv('GMAIL_USER')
    sender_password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not sender_email or not sender_password:
        print("[EMAIL] Missing credentials - skipping email")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = f"Nueva Clasificación Académica: {student_data['applicant_name']}"
    
    body = f"""
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
    
    msg.attach(MIMEText(body, 'html'))
    
    # Attach DOCX file
    try:
        with open(docx_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(docx_path)}')
            msg.attach(part)
    except Exception as e:
        print(f"[EMAIL] Error attaching file: {e}")
        return False
    
    # Send email with timeout
    try:
        print(f"[EMAIL] Connecting to SMTP server...")
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
        server.starttls()
        
        print(f"[EMAIL] Logging in...")
        server.login(sender_email, sender_password)
        
        print(f"[EMAIL] Sending message...")
        server.send_message(msg)
        server.quit()
        
        print(f"[EMAIL] Successfully sent to {recipient}")
        return True
        
    except smtplib.SMTPException as e:
        print(f"[EMAIL] SMTP error: {e}")
        return False
    except Exception as e:
        print(f"[EMAIL] Error sending email: {e}")
        return False