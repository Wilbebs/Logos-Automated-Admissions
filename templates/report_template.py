from datetime import datetime

def get_report_structure(student_data, classification):
    return {
        "header": {
            "title": "UNIVERSIDAD CRISTIANA DE LOGOS",
            "subtitle": "Reporte de Clasificación Académica",
            "logo_path": None,
        },
        
        "metadata": {
            "generated_date": datetime.now().strftime('%d de %B de %Y'),
            "document_type": "Clasificación Académica Automatizada",
            "system_version": "v1.0"
        },
        
        "sections": [
            {
                "title": "INFORMACIÓN DEL SOLICITANTE",
                "type": "key_value_pairs",
                "content": [
                    {"label": "Nombre Completo", "value": student_data['applicant_name']},
                    {"label": "Correo Electrónico", "value": student_data['email']},
                    {"label": "Teléfono", "value": student_data.get('phone', 'No proporcionado')},
                    {"label": "Programa de Interés", "value": student_data['program_interest']},
                    {"label": "Nivel Educativo Actual", "value": student_data['education_level']},
                ]
            },
            
            {
                "title": "RECOMENDACIÓN ACADÉMICA",
                "type": "recommendation",
                "content": {
                    "level": {
                        "label": "Nivel Recomendado",
                        "value": classification['recommended_level'],
                        "highlight": True,
                        "color": "blue"
                    },
                    "programs": {
                        "label": "Programas Sugeridos",
                        "value": classification['recommended_programs'],
                        "type": "bullet_list"
                    },
                    "confidence": {
                        "label": "Nivel de Confianza",
                        "value": f"{classification.get('confidence_score', 'N/A')}/10",
                        "show_warning": classification.get('confidence_score', 10) < 5
                    }
                }
            },
            
            {
                "title": "JUSTIFICACIÓN",
                "type": "paragraph",
                "content": classification['justification']
            },
            
            {
                "title": "EXPERIENCIA MINISTERIAL",
                "type": "paragraph",
                "content": student_data.get('ministerial_experience', 'No proporcionado')
            },
            
            {
                "title": "NOTAS PARA ADMISIONES",
                "type": "alert_box",
                "content": classification['admissions_notes'],
                "alert_level": "warning" if classification.get('confidence_score', 10) < 5 else "info"
            }
        ],
        
        "footer": {
            "text": "Documento generado automáticamente por el Sistema de Clasificación Académica de UCL.",
            "disclaimer": "La recomendación es una sugerencia basada en análisis automatizado. La decisión final corresponde al equipo de admisiones."
        }
    }