"""
Form Detector - Identifies which form was submitted
Works with your existing form config files
"""

# Import all form configurations
import estados_unidos
import latinoamerica
import experiencia_ministerial
import recomendacion_pastoral

# Registry of all forms
ALL_FORMS = [
    estados_unidos,
    latinoamerica,
    experiencia_ministerial,
    recomendacion_pastoral
]


def detect_form(raw_data: dict) -> dict:
    """
    Detect which form was submitted based on the data.
    
    Args:
        raw_data: Raw webhook data from MachForm
        
    Returns:
        Form module (estados_unidos, latinoamerica, etc.) or None
    """
    
    # Method 1: Check detection_fields
    for form_module in ALL_FORMS:
        config = form_module.FORM_CONFIG
        detection_fields = config.get("detection_fields", [])
        
        # Count how many detection fields are present
        matches = sum(1 for field in detection_fields if field in raw_data)
        
        # If most detection fields match, this is likely the form
        if matches >= len(detection_fields) * 0.6:  # 60% match threshold
            print(f"[DETECTOR] Detected: {config['form_name']} (Method 1: detection_fields)")
            return form_module
    
    # Method 2: Check field mappings overlap
    best_match = None
    best_score = 0
    
    for form_module in ALL_FORMS:
        config = form_module.FORM_CONFIG
        mappings = config.get("field_mappings", {})
        
        # Count how many mapped fields are present
        matches = sum(1 for element_id in mappings.keys() if element_id in raw_data)
        total_fields = len(mappings)
        score = matches / total_fields if total_fields > 0 else 0
        
        if score > best_score:
            best_score = score
            best_match = form_module
    
    if best_score >= 0.3:  # 30% of fields match
        print(f"[DETECTOR] Detected: {best_match.FORM_CONFIG['form_name']} (Method 2: field overlap, score: {best_score:.2f})")
        return best_match
    
    # Could not detect
    print(f"[DETECTOR] ⚠️ Could not identify form type (best score: {best_score:.2f})")
    return None


def extract_student_data(raw_data: dict) -> dict:
    """
    Detect form and extract standardized student data.
    
    Args:
        raw_data: Raw webhook data
        
    Returns:
        Standardized student data dict
    """
    form_module = detect_form(raw_data)
    
    if form_module and hasattr(form_module, 'extract_student_data'):
        return form_module.extract_student_data(raw_data)
    else:
        # Fallback: return raw data with basic structure
        print("[DETECTOR] Using fallback extraction")
        return {
            "form_id": "unknown",
            "form_name": "Unknown Form",
            "applicant_name": raw_data.get("element_1", "Unknown"),
            "email": raw_data.get("element_14", "No email"),
            "raw_data": raw_data
        }