"""
Form Configuration: Formulario de Experiencia Ministerial
Detailed ministry history and professional experience form
"""

from configs.base_form import BaseFormConfig
from typing import Dict, List


class ExperienciaMinisterialForm(BaseFormConfig):
    """
    Configuration for "Formulario de Experiencia Ministerial" form.
    This form captures detailed ministry history, professional experience,
    and personal skills to enrich the classification process.
    """
    
    @property
    def form_id(self) -> str:
        return "experiencia_ministerial"
    
    @property
    def form_name(self) -> str:
        return "Formulario de Experiencia Ministerial"
    
    @property
    def detection_fields(self) -> List[str]:
        """
        Unique fields that identify this as the Experiencia Ministerial form.
        Look for ministry-specific questions that don't appear in other forms.
        
        NOTE: Update these with actual element IDs after testing.
        """
        return [
            'element_10',  # Nombre de la Iglesia (church name - unique structure)
            'element_15',  # ¿Hace cuántos años que asiste a la Iglesia?
            'element_20',  # Liste los ministerios en los que ha estado involucrado
            # These are guesses - verify with actual webhook
        ]
    
    @property
    def field_mappings(self) -> Dict[str, str]:
        """
        Maps Experiencia Ministerial form fields to standardized names.
        
        NOTE: Element IDs are ESTIMATED. Verify with actual webhook payload.
        """
        return {
            # DATOS PERSONALES
            'element_1': 'applicant_first_name',      # Nombre
            'element_2': 'applicant_last_name',       # Apellido
            'element_3': 'address_line1',             # Dirección
            'element_4': 'address_line2',             # Dirección (continuación)
            'element_5': 'city',                      # Ciudad
            'element_6': 'state',                     # Estado / Provincia
            'element_7': 'postal_code',               # Código postal
            'element_8': 'country',                   # País
            'element_9': 'email',                     # Correo Electrónico
            'element_10': 'email_confirm',            # Confirmar Correo
            'element_11': 'phone',                    # Teléfono
            'element_12': 'whatsapp',                 # # de Whatsapp
            'element_13': 'facebook',                 # Facebook
            'element_14': 'instagram',                # Instagram
            'element_15': 'linkedin',                 # Linkedin
            'element_16': 'skype',                    # Skype
            
            # DATOS DE LA IGLESIA
            'element_17': 'church_name',              # Nombre de la Iglesia
            'element_18': 'pastor_name',              # Nombre del Pastor
            'element_19': 'church_address_line1',     # Dirección
            'element_20': 'church_address_line2',     # Dirección (continuación)
            'element_21': 'church_city',              # Ciudad
            'element_22': 'church_state',             # Estado
            'element_23': 'church_postal_code',       # Código postal
            'element_24': 'church_country',           # País
            'element_25': 'church_phone',             # Teléfono
            
            # EXPERIENCIA MINISTERIAL
            'element_26': 'years_attending_church',   # ¿Hace cuántos años que asiste?
            'element_27': 'years_pastoring',          # Si es Pastor ¿Desde cuándo?
            'element_28': 'weekly_attendance_freq',   # ¿Cuántas veces asiste por semana?
            'element_29': 'denomination',             # ¿A qué denominación pertenece?
            'element_30': 'financial_support',        # ¿Apoya a la Iglesia Financieramente? (checkboxes)
            'element_31': 'ministry_position',        # Es usted: Anciano/Evangelista/etc (checkboxes)
            'element_32': 'affiliation_group',        # ¿Con qué clase de grupo mantiene afiliación?
            
            # Detailed ministry questions (text areas)
            'element_33': 'ministries_involved',      # Liste los ministerios involucrados
            'element_34': 'biblical_training',        # Resuma entrenamiento Bíblico
            'element_35': 'seminars_workshops',       # Liste seminarios/talleres
            'element_36': 'church_tasks',             # Enumere tareas en la iglesia
            'element_37': 'ministry_achievements',    # Liste logros sobresalientes
            'element_38': 'important_seminars',       # Enumere seminarios importantes asistidos
            'element_39': 'devotional_life',          # Descripción de vida devocional
            'element_40': 'ministerial_submission',   # ¿A quién está sometido ministerialmente?
            'element_41': 'influential_ministry',     # ¿Qué ministerio le ha influenciado?
            'element_42': 'reference_ministries',     # Tres ministerios de referencia
            'element_43': 'best_friends',             # Tres mejores amigos
            'element_44': 'testimony_summary',        # Resuma su Testimonio
            
            # EXPERIENCIA PROFESIONAL
            'element_45': 'professional_area',        # Área de desempeño profesional (checkboxes)
            'element_46': 'profession_specific',      # Profesión u Oficio (Especifique)
            'element_47': 'years_experience',         # Años de Experiencia
            'element_48': 'personal_skills',          # Habilidades Personales (checkboxes)
            'element_49': 'software_tools',           # Software o Herramientas que Maneja
            
            # Document uploads
            'element_50': 'documents_upload',         # Si desea adjuntar documentos
            'element_51': 'documents_list',           # Liste los documentos que envía
            
            # System fields
            'entry_no': 'submission_id',
            'date_created': 'submitted_at',
            'form_id': 'form_identifier'
        }
    
    @property
    def required_fields(self) -> List[str]:
        """
        Required fields for Experiencia Ministerial form.
        Most fields are optional to allow flexibility.
        """
        return [
            'applicant_first_name',
            'applicant_last_name',
            'email',
            'whatsapp',  # Required in form
            'church_name',  # Required in form
            'pastor_name',  # Required in form
            'years_attending_church',  # Required in form
            'denomination',  # Required in form
            'ministry_position',  # Required in form
            'professional_area',  # Required in form
            'profession_specific',  # Required in form
        ]
    
    @property
    def classification_config(self) -> Dict:
        """
        Experiencia Ministerial provides RICH context for classification.
        This form heavily weights ministry experience.
        """
        return {
            'use_default_prompt': False,  # Use custom prompt for this form
            'custom_prompt_additions': '''
This applicant has provided detailed ministry experience through the 
"Formulario de Experiencia Ministerial". Weight the following heavily:

1. Years of active ministry service
2. Specific ministry roles and responsibilities
3. Leadership experience and achievements
4. Biblical/theological training received
5. Professional skills that complement ministry
6. Pastoral references and recommendations

Consider that completion of this form indicates serious commitment 
to theological education and ministry preparation.
            ''',
            'weight_ministry_experience': True,  # HEAVILY weighted
            'weight_education_level': True,
            'weight_professional_experience': True,
            'target_audience': 'Committed ministry leaders and workers',
            'form_indicates_seriousness': True
        }
    
    def get_ministry_summary(self, raw_data: Dict) -> str:
        """
        Generate a comprehensive ministry summary from this form's data.
        This is much more detailed than the brief summary from Solicitud forms.
        """
        extracted = self.extract_all_fields(raw_data)
        
        summary = f"""
EXPERIENCIA MINISTERIAL DETALLADA

Iglesia: {extracted.get('church_name', 'No especificado')}
Pastor: {extracted.get('pastor_name', 'No especificado')}
Denominación: {extracted.get('denomination', 'No especificado')}
Años asistiendo: {extracted.get('years_attending_church', 'N/A')}
Años pastoreando: {extracted.get('years_pastoring', 'N/A')}

Posición Ministerial: {extracted.get('ministry_position', 'No especificado')}

Ministerios en los que ha participado:
{extracted.get('ministries_involved', 'No proporcionado')}

Entrenamiento Bíblico Recibido:
{extracted.get('biblical_training', 'No proporcionado')}

Logros Ministeriales:
{extracted.get('ministry_achievements', 'No proporcionado')}

Vida Devocional:
{extracted.get('devotional_life', 'No proporcionado')}

EXPERIENCIA PROFESIONAL

Área: {extracted.get('professional_area', 'No especificado')}
Profesión: {extracted.get('profession_specific', 'No especificado')}
Años de Experiencia: {extracted.get('years_experience', 'N/A')}
Habilidades: {extracted.get('personal_skills', 'No especificado')}
        """.strip()
        
        return summary
    
    def calculate_ministry_score(self, raw_data: Dict) -> int:
        """
        Calculate a ministry experience score (0-100) based on form data.
        This can be used to enhance classification decisions.
        """
        extracted = self.extract_all_fields(raw_data)
        score = 0
        
        # Years attending church (max 20 points)
        try:
            years_attending = int(extracted.get('years_attending_church', '0'))
            score += min(years_attending * 2, 20)
        except (ValueError, TypeError):
            pass
        
        # Years pastoring (max 20 points)
        try:
            years_pastoring = int(extracted.get('years_pastoring', '0'))
            score += min(years_pastoring * 4, 20)
        except (ValueError, TypeError):
            pass
        
        # Ministry position (max 15 points)
        position = extracted.get('ministry_position', '').lower()
        if 'pastor' in position:
            score += 15
        elif 'leader' in position or 'líder' in position:
            score += 12
        elif 'minister' in position or 'ministro' in position:
            score += 10
        elif position:
            score += 8
        
        # Has detailed ministry involvement (max 15 points)
        if len(extracted.get('ministries_involved', '')) > 50:
            score += 15
        elif len(extracted.get('ministries_involved', '')) > 20:
            score += 10
        
        # Biblical training (max 10 points)
        if len(extracted.get('biblical_training', '')) > 50:
            score += 10
        elif len(extracted.get('biblical_training', '')) > 20:
            score += 5
        
        # Has achievements (max 10 points)
        if len(extracted.get('ministry_achievements', '')) > 50:
            score += 10
        elif len(extracted.get('ministry_achievements', '')) > 20:
            score += 5
        
        # Professional experience (max 10 points)
        if extracted.get('profession_specific'):
            score += 5
        if extracted.get('years_experience'):
            score += 5
        
        return min(score, 100)  # Cap at 100