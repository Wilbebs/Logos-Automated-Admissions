"""
Form Registry - Central registry for all form configurations
"""

from typing import Dict, Optional, Type
from configs.base_form import BaseFormConfig
from configs.forms.estados_unidos import EstadosUnidosForm
from configs.forms.latinoamerica import LatinoamericaForm
from configs.forms.experiencia_ministerial import ExperienciaMinisterialForm
from configs.forms.recomendacion_pastoral import RecomendacionPastoralForm


class FormRegistry:
    """
    Central registry that manages all form configurations.
    Add new forms here as they're created.
    """
    
    def __init__(self):
        self._forms: Dict[str, BaseFormConfig] = {}
        self._register_all_forms()
    
    def _register_all_forms(self):
        """Register all available form configurations"""
        # Register Estados Unidos form (currently working)
        self.register(EstadosUnidosForm())
        
        # Register Latinoamérica form
        self.register(LatinoamericaForm())
        
        # Register Experiencia Ministerial form
        self.register(ExperienciaMinisterialForm())
        
        # Register Recomendación Pastoral form
        self.register(RecomendacionPastoralForm())
        
        # TODO: Add more forms here as they're created:
        # self.register(OtherForm())
    
    def register(self, form_config: BaseFormConfig):
        """
        Register a form configuration.
        
        Args:
            form_config: Instance of a form configuration class
        """
        if form_config.form_id in self._forms:
            print(f"[WARNING] Form '{form_config.form_id}' is already registered. Overwriting.")
        
        self._forms[form_config.form_id] = form_config
        print(f"[REGISTRY] Registered form: {form_config.form_name} (ID: {form_config.form_id})")
    
    def get_form(self, form_id: str) -> Optional[BaseFormConfig]:
        """
        Get a form configuration by its ID.
        
        Args:
            form_id: The form's unique identifier
            
        Returns:
            Form configuration or None if not found
        """
        return self._forms.get(form_id)
    
    def get_all_forms(self) -> Dict[str, BaseFormConfig]:
        """Get all registered form configurations"""
        return self._forms.copy()
    
    def list_forms(self) -> list:
        """Get list of all registered form IDs and names"""
        return [
            {
                'form_id': form.form_id,
                'form_name': form.form_name,
                'detection_fields': form.detection_fields
            }
            for form in self._forms.values()
        ]
    
    def detect_form(self, raw_data: Dict) -> Optional[BaseFormConfig]:
        """
        Detect which form was submitted based on unique fields in the data.
        
        Args:
            raw_data: Raw form submission data
            
        Returns:
            Detected form configuration or None if no match
        """
        submitted_fields = set(raw_data.keys())
        
        # Try to match based on detection fields
        best_match = None
        best_match_score = 0
        
        for form_config in self._forms.values():
            detection_fields = set(form_config.detection_fields)
            matches = detection_fields.intersection(submitted_fields)
            match_score = len(matches)
            
            # If all detection fields are present, we have a strong match
            if matches == detection_fields and match_score > best_match_score:
                best_match = form_config
                best_match_score = match_score
        
        if best_match:
            print(f"[FORM DETECTION] Matched: {best_match.form_name} (score: {best_match_score}/{len(best_match.detection_fields)})")
            return best_match
        
        print(f"[FORM DETECTION] No form matched. Submitted fields: {list(submitted_fields)[:10]}...")
        return None
    
    def __len__(self):
        return len(self._forms)
    
    def __repr__(self):
        return f"<FormRegistry forms={len(self._forms)}>"


# Global registry instance
_registry = None

def get_registry() -> FormRegistry:
    """Get the global form registry instance (singleton pattern)"""
    global _registry
    if _registry is None:
        _registry = FormRegistry()
    return _registry