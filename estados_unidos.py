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
        "element_1_1": "applicant_title",
        "element_1_2": "applicant_name_prefix",
        "element_1": "applicant_first_name",
        "element_2": "applicant_last_name",
        "element_3": "gender",
        "element_4": "study_level_selected",
        "element_5": "program_interest",
        
        # Address
        "element_6": "street_address",
        "element_7": "city",
        "element_8": "state",
        "element_9": "postal_code",
        "element_10": "country",
        
        # Contact
        "element_11": "phone_home",
        "element_12": "phone_work",
        "element_13": "phone_mobile",
        "element_14": "email",
        "element_15": "email_confirm",
        "element_16": "email_secondary",
        "element_17": "website",
        "element_18": "whatsapp",
        "element_19": "skype",
        "element_20": "facebook",
        "element_21": "instagram",
        "element_22": "linkedin",
        "element_23": "language_preferred",
        
        # Personal Information Section
        "element_24": "date_of_birth",
        "element_25": "state_of_birth",
        "element_26": "birth_country",
        "element_27": "marital_status",
        "element_28": "citizenship_country",
        "element_29": "emergency_contact",
        "element_30": "emergency_relationship",
        "element_31": "emergency_phone",
        
        # Ministry Information
        "element_32": "ministry_role",
        "element_33": "ordination_year",
        "element_34": "church_name",
        "element_35": "years_attending",
        "element_36": "years_pastoring",
        "element_37": "church_attendance",
        "element_38": "denomination",
        "element_39": "ministry_summary",
        
        # Education
        "element_40": "high_school_completed",
        "element_41": "high_school_name",
        "element_42": "high_school_city",
        "element_43": "high_school_state",
        "element_44": "high_school_country",
        "element_45": "high_school_grad_year",
        
        # Document checklist
        "element_70": "doc_high_school",
        "element_71": "doc_goals",
        "element_72": "doc_bachelor",
        "element_73": "doc_associate",
        "element_74": "doc_postgrad",
        "element_75": "doc_transcripts",
        
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