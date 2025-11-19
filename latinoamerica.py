"""Latinoamerica Form Configuration"""

FORM_CONFIG = {
    "form_id": "latinoamerica",
    "form_name": "Solicitud Oficial de Admisión Latinoamérica",
    "detection_fields": ["element_1", "element_2", "element_3"],
    "field_mappings": {
        "element_1": "applicant_title",
        "element_2": "applicant_first_name",
        "element_3": "applicant_last_name",
        "element_4": "gender",
        "element_16": "email",
        "element_39": "denomination",
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
    student_data["education_level"] = student_data.get("study_level_selected", "No especificado")
    student_data["ministerial_experience"] = "No especificado"
    student_data["background"] = "No especificado"
    student_data["program_interest"] = student_data.get("program_interest", "No especificado")
    return student_data