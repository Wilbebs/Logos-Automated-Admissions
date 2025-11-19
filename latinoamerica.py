"""
Form Configuration: Solicitud Oficial de Admisión Latinoamérica
Based on actual form structure from MachForm
"""

from configs.base_form import BaseFormConfig
from typing import Dict, List


class LatinoamericaForm(BaseFormConfig):
    """
    Configuration for "Solicitud Oficial de Admisión Latinoamérica" form.
    Similar to Estados Unidos but with regional differences.
    """
    
    @property
    def form_id(self) -> str:
        return "latinoamerica"
    
    @property
    def form_name(self) -> str:
        return "Solicitud Oficial de Admisión Latinoamérica"
    
    @property
    def detection_fields(self) -> List[str]:
        """
        Unique fields that identify this as the Latinoamérica form.
        Look for Spanish-specific field labels or form identifiers.
        These will need to be verified with actual webhook data.
        """
        return [
            'element_1',    # Should have "Prefijo de Nombre / Name Prefix"
            'element_2',    # Nombre / First Name
            'element_3',    # Apellido / Last Name
            # Note: Once you test, update these with actual unique element IDs
        ]
    
    @property
    def field_mappings(self) -> Dict[str, str]:
        """
        Maps Latinoamérica form element IDs to standardized field names.
        
        NOTE: These element IDs are ESTIMATED and need to be verified
        when you submit a test form and check the webhook payload.
        """
        return {
            # Name fields (ESTIMATED - verify with real submission)
            'element_1': 'applicant_title',        # Prefijo de Nombre
            'element_2': 'applicant_first_name',   # Nombre
            'element_3': 'applicant_last_name',    # Apellido
            'element_4': 'gender',                 # Género
            'element_5': 'language_preferred',     # Lenguaje Preferido
            
            # Study level and area
            'element_6': 'study_level_selected',   # Niveles de Estudio
            'element_7': 'program_interest',       # Área de Estudios
            
            # Address
            'element_8': 'street_address',         # Calle
            'element_9': 'city',                   # Ciudad
            'element_10': 'state',                 # Estado
            'element_11': 'postal_code',           # Código Postal
            'element_12': 'country',               # País
            
            # Contact
            'element_13': 'phone_home',            # Teléfono de Casa
            'element_14': 'phone_work',            # Teléfono del Trabajo
            'element_15': 'phone_mobile',          # Teléfono Móvil
            'element_16': 'email',                 # Correo Electrónico I (REQUIRED)
            'element_17': 'email_confirm',         # Confirmar Correo
            'element_18': 'email_secondary',       # Correo Electrónico II
            'element_19': 'website',               # Página Web
            'element_20': 'whatsapp',              # # de Whatsapp
            'element_21': 'skype',                 # Skype
            'element_22': 'facebook',              # Facebook
            'element_23': 'instagram',             # Instagram
            'element_24': 'linkedin',              # LinkedIn
            
            # Personal Information
            'element_25': 'date_of_birth',         # Fecha de Nacimiento
            'element_26': 'state_of_birth',        # Estado de Nacimiento
            'element_27': 'birth_country',         # País de Nacimiento
            'element_28': 'marital_status',        # Estado Civil
            'element_29': 'citizenship_country',   # País de Origen
            'element_30': 'emergency_contact',     # Familiar o Amigo Cercano
            'element_31': 'emergency_relationship', # Relación
            'element_32': 'emergency_phone',       # Número de Teléfono
            
            # Ministry Information
            'element_33': 'ministry_role',         # Ministry/Ministerio
            'element_34': 'ordination_year',       # En que año fue ordenado
            'element_35': 'church_name',           # Church/Iglesia
            'element_36': 'years_attending',       # ¿Desde cuándo asiste?
            'element_37': 'years_pastoring',       # ¿Desde cuándo pastorea?
            'element_38': 'church_attendance',     # ¿Cuántas personas asisten?
            'element_39': 'denomination',          # ¿A qué denominación pertenece?
            'element_40': 'ministry_summary',      # Resumen de vida en ministerio
            
            # High School
            'element_41': 'high_school_completed', # Completo Su Escuela Secundaria
            'element_42': 'high_school_name',      # Nombre de la Escuela
            'element_43': 'high_school_city',      # Ciudad
            'element_44': 'high_school_state',     # Estado
            'element_45': 'high_school_country',   # País
            'element_46': 'high_school_grad_year', # Año en que se Graduó
            
            # GED
            'element_47': 'ged_state',             # Estado dondé completó su GED
            'element_48': 'ged_type',              # Tipo de Diploma
            'element_49': 'ged_date',              # Fecha en que completó su GED
            
            # Education levels (will need to verify actual field names)
            'element_50': 'associate_degree',      # Técnico
            'element_51': 'bachelor_degree',       # Licenciatura
            'element_52': 'master_degree',         # Maestría
            'element_53': 'doctoral_degree',       # Doctorado
            'element_54': 'other_degree',          # Otro
            
            # System fields
            'entry_no': 'submission_id',
            'date_created': 'submitted_at',
            'form_id': 'form_identifier'
        }
    
    @property
    def required_fields(self) -> List[str]:
        """Required fields for Latinoamérica form"""
        return [
            'applicant_first_name',
            'applicant_last_name',
            'email',
            'country',  # Important for regional form
            'denomination',  # Required in form
            'program_interest'
        ]
    
    @property
    def classification_config(self) -> Dict:
        """
        Latinoamérica form has regional considerations.
        Lower fee ($40 vs $60) suggests different regional context.
        """
        return {
            'use_default_prompt': True,
            'custom_prompt_additions': 'Applicant is from Latin America region. Consider regional educational context and ministry background.',
            'weight_ministry_experience': True,
            'weight_education_level': True,
            'target_audience': 'Latin American students',
            'application_fee': '$40 USD'
        }