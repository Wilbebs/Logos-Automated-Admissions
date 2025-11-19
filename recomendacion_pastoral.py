"""Recomendacion Pastoral Form Configuration"""

FORM_CONFIG = {
    "form_id": "recomendacion_pastoral",
    "form_name": "Formulario de Recomendación Pastoral",
    "detection_fields": ["element_18", "element_28", "element_41"],
    "field_mappings": {
        "element_1": "applicant_first_name",
        "element_2": "applicant_last_name",
        "element_9": "applicant_email",
        "element_18": "pastor_name",
        # Add more as you test
    },
    "required_fields": ["applicant_first_name", "applicant_last_name"]
}

def extract_student_data(raw_data: dict) -> dict:
    mappings = FORM_CONFIG["field_mappings"]
    student_data = {"form_id": FORM_CONFIG["form_id"], "form_name": FORM_CONFIG["form_name"]}
    for element_id, field_name in mappings.items():
        if element_id in raw_data:
            student_data[field_name] = raw_data[element_id]
    student_data["applicant_name"] = f"{student_data.get('applicant_first_name', '')} {student_data.get('applicant_last_name', '')}".strip()
    student_data["email"] = student_data.get("applicant_email", "No email")
    student_data["education_level"] = "No especificado"
    student_data["ministerial_experience"] = f"Pastor: {student_data.get('pastor_name', 'N/A')}"
    student_data["background"] = "Recomendación Pastoral"
    student_data["program_interest"] = "No especificado"
    return student_data