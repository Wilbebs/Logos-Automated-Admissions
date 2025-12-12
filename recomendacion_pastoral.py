"""Recomendacion Pastoral Form Configuration"""

FORM_CONFIG = {
    "form_id": "recomendacion_pastoral",
    "form_name": "Formulario de Recomendación Pastoral",
    "detection_fields": ["element_18", "element_41"],  # ← UNIQUE: pastor_name + rating field
    "field_mappings": {
        "element_3":  "applicant_first_name",
        "element_77": "applicant_last_name",
        "element_79": "applicant_email",
        "element_12": "pastor_name",
        "element_11": "church_name",
        "element_67": "pastor_email",
        "element_4":  "date_of_birth",
        "element_78": "street_address",
        "element_9":  "phone",
        "element_72": "rating_commitment",
    },
    "required_fields": ["applicant_first_name", "applicant_last_name"],
    "named_mappings": {
        "applicant_first_name": "Nombre",
        "applicant_last_name": "Apellido",
        "applicant_email": "CorreoElectrónico", # Note: Warning about duplicate keys in source, preferring element ID if available
        "pastor_name": "NombreDelPastor",
        "church_name": "NombreDeLaIglesia",
        "date_of_birth": "FechaDeNacimiento",
        "street_address": "Dirección",
        "phone": "TeléfonoCelular"
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