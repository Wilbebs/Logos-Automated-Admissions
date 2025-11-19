"""Experiencia Ministerial Form Configuration"""

FORM_CONFIG = {
    "form_id": "experiencia_ministerial",
    "form_name": "Formulario de Experiencia Ministerial",
    "detection_fields": ["element_17", "element_26", "element_33"],
    "field_mappings": {
        "element_1": "applicant_first_name",
        "element_2": "applicant_last_name",
        "element_9": "email",
        "element_17": "church_name",
        "element_26": "years_attending_church",
        # Add more as you test
    },
    "required_fields": ["applicant_first_name", "applicant_last_name", "email"]
}

def extract_student_data(raw_data: dict) -> dict:
    mappings = FORM_CONFIG["field_mappings"]
    student_data = {"form_id": FORM_CONFIG["form_id"], "form_name": FORM_CONFIG["form_name"]}
    for element_id, field_name in mappings.items():
        if element_id in raw_data:
            student_data[field_name] = raw_data[element_id]
    student_data["applicant_name"] = f"{student_data.get('applicant_first_name', '')} {student_data.get('applicant_last_name', '')}".strip()
    student_data["education_level"] = "No especificado"
    student_data["ministerial_experience"] = f"Iglesia: {student_data.get('church_name', 'N/A')}"
    student_data["background"] = "Experiencia Ministerial"
    student_data["program_interest"] = "No especificado"
    return student_data