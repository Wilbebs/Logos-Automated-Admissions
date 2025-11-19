"""
Form Configuration: Formulario de Recomendación Pastoral
Pastor's recommendation and character reference form
"""

from configs.base_form import BaseFormConfig
from typing import Dict, List


class RecomendacionPastoralForm(BaseFormConfig):
    """
    Configuration for "Formulario de Recomendación Pastoral" form.
    
    This form is filled out by a PASTOR/CHURCH LEADER (not the applicant).
    It provides third-party verification and character assessment.
    
    IMPORTANT: This form should be TRACKED but final judgment should 
    remain with HUMAN admissions staff due to its subjective nature.
    """
    
    @property
    def form_id(self) -> str:
        return "recomendacion_pastoral"
    
    @property
    def form_name(self) -> str:
        return "Formulario de Recomendación Pastoral"
    
    @property
    def detection_fields(self) -> List[str]:
        """
        Unique fields that identify this as the Recomendación Pastoral form.
        This form has VERY distinct questions that pastors answer about applicants.
        
        NOTE: Update with actual element IDs after testing.
        """
        return [
            'element_10',  # Nombre del Pastor (unique structure)
            'element_15',  # ¿Cuánto tiempo ha conocido al aplicante?
            'element_20',  # Rating scales (unique to this form)
            # These are guesses - verify with webhook
        ]
    
    @property
    def field_mappings(self) -> Dict[str, str]:
        """
        Maps Recomendación Pastoral form fields to standardized names.
        
        NOTE: Element IDs are ESTIMATED. Verify with actual webhook.
        """
        return {
            # INFORMACION PERSONAL DEL APLICANTE (Applicant Info)
            'element_1': 'applicant_first_name',      # Nombre
            'element_2': 'applicant_last_name',       # Apellido
            'element_3': 'applicant_birth_date',      # Fecha de nacimiento
            'element_4': 'applicant_address_line2',   # Address Line 2
            'element_5': 'applicant_city',            # City
            'element_6': 'applicant_state',           # State/Province
            'element_7': 'applicant_postal_code',     # Postal/Zip Code
            'element_8': 'applicant_country',         # Country
            'element_9': 'applicant_email',           # Correo Electrónico
            'element_10': 'applicant_email_confirm',  # Confirmar Correo
            'element_11': 'applicant_phone_mobile',   # Teléfono celular
            'element_12': 'applicant_phone_alt',      # Teléfono alterno
            'element_13': 'applicant_whatsapp',       # # de Whatsapp
            'element_14': 'applicant_skype',          # Skype
            'element_15': 'applicant_facebook',       # Facebook
            'element_16': 'applicant_instagram',      # Instagram
            'element_17': 'applicant_linkedin',       # Linkedin
            
            # INFORMACION DEL PASTOR (Pastor Info - Person FILLING the form)
            'element_18': 'pastor_name',              # Nombre del Pastor
            'element_19': 'church_name',              # Nombre de la Iglesia
            'element_20': 'denomination',             # Denominación
            'element_21': 'church_address',           # Dirección de la Iglesia
            'element_22': 'church_city',              # Ciudad
            'element_23': 'church_state',             # Estado
            'element_24': 'church_postal_code',       # Código Postal
            'element_25': 'pastor_email',             # Correo Electrónico del Pastor
            'element_26': 'pastor_phone',             # Teléfono del Pastor
            'element_27': 'recommendation_date',      # Fecha
            
            # ASSESSMENT QUESTIONS
            'element_28': 'time_known_applicant',     # ¿Cuánto tiempo ha conocido al aplicante?
            'element_29': 'how_well_known',           # ¿Cuán bien conoce al aplicante?
            'element_30': 'professed_salvation',      # ¿Cree que ha profesado ser salvo?
            'element_31': 'evidence_of_faith',        # ¿Observa evidencias de Fe?
            'element_32': 'church_member',            # ¿Es miembro de su iglesia?
            'element_33': 'participation_level',      # Nivel de participación
            'element_34': 'attitude_terms',           # Términos que describen actitud (checkboxes)
            'element_35': 'church_involvement',       # Envolvimiento en iglesia local
            
            # Negative behaviors (question 9)
            'element_36': 'smokes',                   # fuma
            'element_37': 'drinks',                   # bebe
            'element_38': 'uses_substances',          # usa sustancias ilegales
            'element_39': 'negative_comments',        # Comentarios sobre comportamientos
            
            'element_40': 'pays_debts',               # Es responsable en pagar deudas
            
            # RATING SCALES (Bajo Promedio, Promedio, Sobre Promedio, Bueno, Excepcional, No he podido observar)
            'element_41': 'rating_christian_commitment',  # Compromiso Cristiano
            'element_42': 'rating_integrity',             # Integridad y Carácter
            'element_43': 'rating_leadership',            # Potencial de Liderazgo
            'element_44': 'rating_morality',              # Moral y Ética
            'element_45': 'rating_speaking',              # Habilidad para hablar
            'element_46': 'rating_honesty',               # Honestidad
            'element_47': 'rating_cooperation',           # Cooperación
            'element_48': 'rating_appearance',            # Apariencia Personal
            'element_49': 'rating_confidence',            # Confidencia
            'element_50': 'rating_family',                # Orientación Familiar
            'element_51': 'rating_achievements',          # Logros en el Ministerio
            'element_52': 'rating_physical_health',       # Salud Física
            'element_53': 'rating_consistency',           # Constancia
            'element_54': 'rating_resistance_change',     # Se resiste a los cambios
            'element_55': 'rating_team_worker',           # Fiel trabajador en equipo
            'element_56': 'rating_consideration',         # Consideración por otros
            'element_57': 'rating_shows_love',            # Muestras de amor
            'element_58': 'rating_persistence',           # Persistencia
            'element_59': 'rating_mental_ability',        # Habilidad mental
            'element_60': 'rating_emotional_stability',   # Estabilidad emocional
            'element_61': 'rating_initiative',            # Iniciativa
            'element_62': 'rating_problem_solver',        # Solucionador de problemas
            'element_63': 'rating_innovative',            # Innovativo
            'element_64': 'rating_multitasker',           # Trata de hacer muchas cosas al mismo tiempo
            
            # FINAL QUESTIONS
            'element_65': 'additional_info',          # Información adicional (text area)
            'element_66': 'recommend_for_program',    # ¿Recomendaría a esta persona?
            'element_67': 'recommendation_comments',  # Comentarios sobre recomendación
            'element_68': 'attitude_toward_authority', # Actitud hacia la autoridad
            'element_69': 'authority_comments',       # Comentarios sobre autoridad
            
            # System fields
            'entry_no': 'submission_id',
            'date_created': 'submitted_at',
            'form_id': 'form_identifier'
        }
    
    @property
    def required_fields(self) -> List[str]:
        """
        Required fields for Recomendación Pastoral form.
        """
        return [
            'applicant_first_name',
            'applicant_last_name',
            'applicant_email',
            'pastor_name',
            'pastor_email',  # Important - verifies pastor filled it
            'pastor_phone',  # Important - verifies pastor filled it
            'time_known_applicant',
            'recommend_for_program',  # Critical field
        ]
    
    @property
    def classification_config(self) -> Dict:
        """
        Recomendación Pastoral is SUBJECTIVE and should be HUMAN-REVIEWED.
        AI should extract and flag, not make final decisions.
        """
        return {
            'use_default_prompt': False,
            'custom_prompt_additions': '''
This is a PASTORAL RECOMMENDATION filled by a church leader.
DO NOT make final classification decisions based solely on this form.

Your role is to:
1. Extract key information (pastor name, church, ratings)
2. Flag any concerning responses (negative behaviors, weak ratings)
3. Summarize the overall recommendation strength
4. Defer final judgment to human admissions staff

This form provides CHARACTER REFERENCE, not academic qualification.
            ''',
            'weight_ministry_experience': False,  # This isn't about experience
            'weight_education_level': False,      # This isn't about education
            'is_third_party_reference': True,     # Critical flag
            'requires_human_review': True,        # ALWAYS require human review
            'target_audience': 'Character/spiritual assessment',
            'form_purpose': 'verification_and_reference'
        }
    
    def calculate_recommendation_strength(self, raw_data: Dict) -> tuple[str, int, List[str]]:
        """
        Analyze the pastoral recommendation and return:
        - Overall strength: "Strong", "Moderate", "Weak", "Negative"
        - Numeric score: 0-100
        - List of flags/concerns
        
        This helps human reviewers quickly assess the recommendation.
        """
        extracted = self.extract_all_fields(raw_data)
        flags = []
        score = 50  # Start at neutral
        
        # Check final recommendation
        recommend = extracted.get('recommend_for_program', '').lower()
        if 'no' in recommend:
            score -= 40
            flags.append("🚨 Pastor does NOT recommend applicant")
        elif 'reservaciones' in recommend or 'reservations' in recommend:
            score -= 20
            flags.append("⚠️ Pastor recommends WITH RESERVATIONS")
        elif 'sí' in recommend or 'si' in recommend or 'yes' in recommend:
            score += 20
        
        # Check negative behaviors
        if extracted.get('smokes', '').lower() == 'si' or extracted.get('smokes', '').lower() == 'sí':
            score -= 10
            flags.append("⚠️ Applicant smokes")
        if extracted.get('drinks', '').lower() == 'si' or extracted.get('drinks', '').lower() == 'sí':
            score -= 10
            flags.append("⚠️ Applicant drinks alcohol")
        if extracted.get('uses_substances', '').lower() == 'si' or extracted.get('uses_substances', '').lower() == 'sí':
            score -= 30
            flags.append("🚨 Applicant uses illegal substances")
        
        # Check debt responsibility
        pays_debts = extracted.get('pays_debts', '').lower()
        if 'no' in pays_debts:
            score -= 15
            flags.append("⚠️ Does not pay debts responsibly")
        
        # Count high ratings (Excepcional, Bueno)
        rating_fields = [f'rating_{x}' for x in ['christian_commitment', 'integrity', 'leadership', 
                                                   'morality', 'honesty', 'cooperation', 'family',
                                                   'emotional_stability', 'problem_solver']]
        
        high_ratings = 0
        low_ratings = 0
        
        for field in rating_fields:
            rating = extracted.get(field, '').lower()
            if 'excepcional' in rating:
                high_ratings += 2
                score += 2
            elif 'bueno' in rating or 'good' in rating:
                high_ratings += 1
                score += 1
            elif 'bajo' in rating or 'low' in rating:
                low_ratings += 1
                score -= 2
        
        if low_ratings > 3:
            flags.append(f"⚠️ Multiple low ratings ({low_ratings} areas)")
        
        # Check attitude toward authority
        authority = extracted.get('attitude_toward_authority', '').lower()
        if 'problemática' in authority or 'problematic' in authority:
            score -= 20
            flags.append("🚨 Problematic attitude toward authority")
        elif 'cuestionable' in authority or 'questionable' in authority:
            score -= 10
            flags.append("⚠️ Questionable attitude toward authority")
        
        # Determine overall strength
        if score >= 70:
            strength = "Strong"
        elif score >= 50:
            strength = "Moderate"
        elif score >= 30:
            strength = "Weak"
        else:
            strength = "Negative"
        
        return strength, min(max(score, 0), 100), flags
    
    def get_pastor_verification_info(self, raw_data: Dict) -> Dict:
        """
        Extract pastor/church info for verification purposes.
        Admissions staff can use this to contact the pastor if needed.
        """
        extracted = self.extract_all_fields(raw_data)
        
        return {
            'pastor_name': extracted.get('pastor_name', 'No proporcionado'),
            'church_name': extracted.get('church_name', 'No proporcionado'),
            'denomination': extracted.get('denomination', 'No proporcionado'),
            'pastor_email': extracted.get('pastor_email', 'No proporcionado'),
            'pastor_phone': extracted.get('pastor_phone', 'No proporcionado'),
            'church_city': extracted.get('church_city', 'No proporcionado'),
            'church_state': extracted.get('church_state', 'No proporcionado'),
            'time_known_applicant': extracted.get('time_known_applicant', 'No proporcionado'),
            'how_well_known': extracted.get('how_well_known', 'No proporcionado'),
            'recommendation_date': extracted.get('recommendation_date', 'No proporcionado')
        }