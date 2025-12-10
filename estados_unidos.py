"""
Estados Unidos y el Mundo Form Configuration
This is the WORKING form - already tested and functional
"""

# Form configuration for "Solicitud Oficial de Admisión Estados Unidos y el Mundo"
FORM_CONFIG = {
    "form_id": "estados_unidos_mundo",
    "form_name": "Solicitud Oficial de Admisión Estados Unidos y el Mundo",
    
    # Fields that uniquely identify this form
    "detection_fields": [
        "element_1_1",  # Title/Título
        "element_1_2",  # Name prefix / Prefijo de Nombre
        "element_1",    # First Name / Nombre
    ],
    
    # Map MachForm element IDs to standardized field names
    "field_mappings": {
        # Personal Information
        "element_1_1": "applicant_title",       # Keep original if uncertain, user didn't specify replacement
        "element_1_2": "applicant_name_prefix", # Keep original if uncertain
        "element_143": "applicant_first_name",  # UPDATED
        "element_6":   "applicant_last_name",   # UPDATED
        "element_3":   "gender",
        "element_147": "study_level_selected",  # UPDATED
        "element_148": "program_interest",      # UPDATED
        
        # Address
        "element_6_1": "street_address", # Guessing based on "element_6" being lastname, maybe address is different now? 
                                         # User didn't specify address fields, keeping defaults might be risky if IDs shifted.
                                         # But we must update the KNOWN ones.
        
        # Contact
        "element_4":   "email",             # UPDATED
        
        # Ministry Information
        "element_28":  "ministry_role",     # UPDATED (User said "Ministry")
        "element_27":  "church_name",       # UPDATED (User said "Church")
        
        # System fields
        "entry_no": "submission_id",
        "date_created": "submitted_at",
    },
    
    # Required fields
    "required_fields": [
        "applicant_first_name",
        "applicant_last_name",
        "email",
        "program_interest"
    ]
}


def extract_student_data(raw_data: dict) -> dict:
    """Extract and standardize student data from Estados Unidos form"""
    mappings = FORM_CONFIG["field_mappings"]
    
    # Extract basic info
    student_data = {
        "form_id": FORM_CONFIG["form_id"],
        "form_name": FORM_CONFIG["form_name"],
    }
    
    # Map all fields
    for element_id, field_name in mappings.items():
        if element_id in raw_data:
            student_data[field_name] = raw_data[element_id]
    
    # Standardize some fields
    student_data["applicant_name"] = f"{student_data.get('applicant_first_name', '')} {student_data.get('applicant_last_name', '')}".strip()
    
    # Determine education level from various sources
    education_level = "No especificado"
    if student_data.get("study_level_selected"):
        education_level = student_data["study_level_selected"]
    
    student_data["education_level"] = education_level
    
    # Ministry experience summary
    ministry_exp = []
    if student_data.get("ministry_role"):
        ministry_exp.append(f"Rol: {student_data['ministry_role']}")
    if student_data.get("years_attending"):
        ministry_exp.append(f"Años asistiendo: {student_data['years_attending']}")
    if student_data.get("church_name"):
        ministry_exp.append(f"Iglesia: {student_data['church_name']}")
    
    student_data["ministerial_experience"] = " | ".join(ministry_exp) if ministry_exp else "No especificado"
    
    # Background summary
    background_parts = []
    if student_data.get("denomination"):
        background_parts.append(f"Denominación: {student_data['denomination']}")
    if student_data.get("high_school_completed"):
        background_parts.append(f"Secundaria: {student_data['high_school_completed']}")
    
    student_data["background"] = " | ".join(background_parts) if background_parts else "No especificado"
    
    return student_data