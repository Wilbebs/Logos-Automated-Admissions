import sys
import os
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from docx_generator import generate_report

def test_report_generation():
    print("Testing Report Generation...")
    
    student_data = {
        'applicant_name': 'Juan Pérez Test',
        'email': 'juan.test@example.com',
        'program_interest': 'Maestría en Teología',
        'education_level': 'Licenciatura en Teología (UCL)',
        'ministerial_experience': 'Pastor asociado por 6 años en la Iglesia Central.'
    }
    
    classification = {
        'recommended_level': 'Postgrado - Maestría',
        'recommended_programs': [
            'Maestría en Divinidad (M.Div)',
            'Maestría en Liderazgo Ministerial'
        ],
        'confidence_score': 92,
        'reasoning': {
            'educational_assessment': 'Verified ministerial bachelor\'s with official transcript.',
            'ministry_experience_assessment': '6 years as associate pastor, substantial leadership.',
            'pastoral_recommendation_assessment': 'Strong verified recommendation from senior pastor.',
            'documents_missing': [],
            'pathway_explanation': None
        },
        'next_steps': ['Enrollment fee payment', 'Course selection']
    }
    
    try:
        report_path = generate_report(student_data, classification)
        print(f"✅ Success! Report generated at: {report_path}")
        return True
    except Exception as e:
        print(f"❌ Failed! Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_report_generation()
