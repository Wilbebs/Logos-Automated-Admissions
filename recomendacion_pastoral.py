"""Recomendacion Pastoral Form Configuration"""

FORM_CONFIG = {
    "form_id": "recomendacion_pastoral",
    "form_name": "Formulario de Recomendación Pastoral",
    "detection_fields": ["element_18", "element_41"],  # ← UNIQUE: pastor_name + rating field
    "field_mappings": {
        "element_3":  "applicant_first_name",   # UPDATED
        "element_77": "applicant_last_name",    # UPDATED
        "element_79": "applicant_email",        # UPDATED
        "element_18": "pastor_name",            # UPDATED (Matches old?)
        "element_28": "time_known",             # Keep existing?
        "element_72": "rating_commitment",      # UPDATED
    },
    "required_fields": ["applicant_first_name", "applicant_last_name"],
    "named_mappings": {
        "applicant_first_name": "FirstNmeNombre",
        "applicant_last_name": "LastNameApellido",
        "applicant_email": "EmailICorreoElectrónicoI"
    }
}

def extract_student_data(raw_data: dict) -> dict:
    mappings = FORM_CONFIG["field_mappings"]
    student_data = {"form_id": FORM_CONFIG["form_id"], "form_name": FORM_CONFIG["form_name"]}
    for element_id, field_name in mappings.items():
        if element_id in raw_data:
            student_data[field_name] = raw_data[element_id]
        else:
            named_key = FORM_CONFIG.get("named_mappings", {}).get(field_name)
            if named_key and named_key in raw_data:
                student_data[field_name] = raw_data[named_key]
    
    student_data["applicant_name"] = f"{student_data.get('applicant_first_name', '')} {student_data.get('applicant_last_name', '')}".strip()
    student_data["email"] = student_data.get("applicant_email", "No email")
    student_data["education_level"] = "No especificado"
    student_data["ministerial_experience"] = f"Pastor: {student_data.get('pastor_name', 'N/A')}"
    student_data["background"] = "Recomendación Pastoral"
    student_data["program_interest"] = "No especificado"
    
    return student_data