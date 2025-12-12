"""Experiencia Ministerial Form Configuration"""

FORM_CONFIG = {
    "form_id": "experiencia_ministerial",
    "form_name": "Formulario de Experiencia Ministerial",
    "detection_fields": ["element_26", "element_33"],  # ← UNIQUE: years_attending + ministry role
    "field_mappings": {
        "element_16": "applicant_first_name",
        "element_67": "applicant_last_name",
        "element_66": "email",
        "element_1":  "church_name",
        "element_55": "years_attending_church",
        "element_64": "ministry_position",
        "element_78": "street_address",
        "element_22": "phone",
        "element_3":  "pastor_name",
        "element_56": "whatsapp"
    },
    "required_fields": ["applicant_first_name", "applicant_last_name", "email"],
    "named_mappings": {
        "applicant_first_name": "Nombre",
        "applicant_last_name": "Apellido",
        "email": "CorreoElectrónico",
        "church_name": "NombreDeLaIglesia",
        "street_address": "DirecciónDeResidencia",
        "phone": "Teléfono",
        "pastor_name": "NombreDelPastor",
        "whatsapp": "DeWhatsapp"
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
    student_data["email"] = student_data.get("email", "No email")
    student_data["education_level"] = "No especificado"
    student_data["ministerial_experience"] = f"Iglesia: {student_data.get('church_name', 'N/A')}"
    student_data["background"] = "Experiencia Ministerial"
    student_data["program_interest"] = "No especificado"
    
    return student_data