"""
Application Tracking System
Tracks which forms have been submitted for each applicant and their status.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum


class ApplicationStatus(Enum):
    """Application status states"""
    PENDING = "pending"  # Initial form submitted, awaiting supporting docs
    IN_REVIEW = "in_review"  # All forms submitted, ready for review
    COMPLETE = "complete"  # Final classification done
    INCOMPLETE = "incomplete"  # Missing required forms


class FormType(Enum):
    """Types of forms in the system"""
    SOLICITUD_OFICIAL = "solicitud_oficial"  # Either US or Latinoamerica
    EXPERIENCIA_MINISTERIAL = "experiencia_ministerial"
    RECOMENDACION_PASTORAL = "recomendacion_pastoral"


@dataclass
class FormSubmission:
    """Represents a single form submission"""
    form_type: str
    form_id: str  # estados_unidos, latinoamerica, etc.
    form_name: str
    submission_id: str
    submitted_at: str
    data_snapshot: Dict  # Key fields for reference


@dataclass
class ApplicantApplication:
    """Represents an applicant's complete application package"""
    applicant_email: str  # Unique identifier
    applicant_name: str
    status: str  # ApplicationStatus value
    created_at: str
    updated_at: str
    forms_submitted: List[FormSubmission]
    required_forms: Set[str]  # Set of form types needed
    classification_results: Optional[Dict] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['required_forms'] = list(data['required_forms'])  # Convert set to list
        return data
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary"""
        data['required_forms'] = set(data['required_forms'])  # Convert list to set
        # Convert form submissions
        data['forms_submitted'] = [
            FormSubmission(**fs) for fs in data.get('forms_submitted', [])
        ]
        return cls(**data)


class ApplicationTracker:
    """
    Tracks applicant applications and form submissions.
    Uses file-based storage for simplicity (can be upgraded to database later).
    """
    
    def __init__(self, storage_path: str = '/tmp/applications_tracking.json'):
        self.storage_path = storage_path
        self.applications: Dict[str, ApplicantApplication] = {}
        self.load()
    
    def load(self):
        """Load applications from file"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.applications = {
                        email: ApplicantApplication.from_dict(app_data)
                        for email, app_data in data.items()
                    }
                print(f"[TRACKER] Loaded {len(self.applications)} applications")
            except Exception as e:
                print(f"[TRACKER] Error loading: {e}")
                self.applications = {}
        else:
            print(f"[TRACKER] No existing tracking file, starting fresh")
    
    def save(self):
        """Save applications to file"""
        try:
            data = {
                email: app.to_dict()
                for email, app in self.applications.items()
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[TRACKER] Saved {len(self.applications)} applications")
        except Exception as e:
            print(f"[TRACKER] Error saving: {e}")
    
    def get_or_create_application(self, email: str, name: str) -> ApplicantApplication:
        """Get existing application or create new one"""
        if email not in self.applications:
            # Determine required forms based on program level
            # For now, all applicants need all forms
            required_forms = {
                FormType.SOLICITUD_OFICIAL.value,
                FormType.EXPERIENCIA_MINISTERIAL.value,
                FormType.RECOMENDACION_PASTORAL.value
            }
            
            self.applications[email] = ApplicantApplication(
                applicant_email=email,
                applicant_name=name,
                status=ApplicationStatus.PENDING.value,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                forms_submitted=[],
                required_forms=required_forms,
                classification_results=None
            )
            print(f"[TRACKER] Created new application for {name} ({email})")
        
        return self.applications[email]
    
    def record_submission(self, email: str, name: str, form_config, student_data: Dict, classification: Dict):
        """
        Record a form submission and update application status.
        
        Args:
            email: Applicant email
            name: Applicant name
            form_config: FormConfig object
            student_data: Standardized student data
            classification: AI classification results
        """
        app = self.get_or_create_application(email, name)
        
        # Determine form type
        form_type = self._determine_form_type(form_config.form_id)
        
        # Create form submission record
        submission = FormSubmission(
            form_type=form_type.value,
            form_id=form_config.form_id,
            form_name=form_config.form_name,
            submission_id=student_data.get('submission_id', 'N/A'),
            submitted_at=datetime.now().isoformat(),
            data_snapshot={
                'program_interest': student_data.get('program_interest'),
                'education_level': student_data.get('education_level'),
                'study_level_selected': student_data.get('study_level_selected')
            }
        )
        
        # Add to forms (replace if same form type)
        app.forms_submitted = [
            f for f in app.forms_submitted if f.form_type != form_type.value
        ]
        app.forms_submitted.append(submission)
        
        # Update classification results (keep most recent)
        app.classification_results = classification
        
        # Update status
        app.updated_at = datetime.now().isoformat()
        app.status = self._calculate_status(app)
        
        # Save
        self.save()
        
        print(f"[TRACKER] Recorded {form_config.form_name} for {name}")
        print(f"[TRACKER] Status: {app.status} | Forms: {len(app.forms_submitted)}/{len(app.required_forms)}")
        
        return app
    
    def _determine_form_type(self, form_id: str) -> FormType:
        """Determine form type from form ID"""
        if form_id in ['estados_unidos_mundo', 'latinoamerica']:
            return FormType.SOLICITUD_OFICIAL
        elif form_id == 'experiencia_ministerial':
            return FormType.EXPERIENCIA_MINISTERIAL
        elif form_id == 'recomendacion_pastoral':
            return FormType.RECOMENDACION_PASTORAL
        else:
            return FormType.SOLICITUD_OFICIAL  # Default
    
    def _calculate_status(self, app: ApplicantApplication) -> str:
        """Calculate application status based on submitted forms"""
        submitted_types = {f.form_type for f in app.forms_submitted}
        
        if submitted_types >= app.required_forms:
            # All required forms submitted
            if app.classification_results:
                return ApplicationStatus.COMPLETE.value
            else:
                return ApplicationStatus.IN_REVIEW.value
        elif FormType.SOLICITUD_OFICIAL.value in submitted_types:
            # At least the main form is submitted
            return ApplicationStatus.PENDING.value
        else:
            return ApplicationStatus.INCOMPLETE.value
    
    def get_application(self, email: str) -> Optional[ApplicantApplication]:
        """Get application by email"""
        return self.applications.get(email)
    
    def get_missing_forms(self, email: str) -> List[str]:
        """Get list of missing forms for an applicant"""
        app = self.applications.get(email)
        if not app:
            return []
        
        submitted_types = {f.form_type for f in app.forms_submitted}
        missing = app.required_forms - submitted_types
        
        # Convert to friendly names
        form_names = {
            FormType.SOLICITUD_OFICIAL.value: "Solicitud Oficial de Admisión",
            FormType.EXPERIENCIA_MINISTERIAL.value: "Formulario de Experiencia Ministerial",
            FormType.RECOMENDACION_PASTORAL.value: "Formulario de Recomendación Pastoral"
        }
        
        return [form_names.get(ft, ft) for ft in missing]
    
    def is_application_complete(self, email: str) -> bool:
        """Check if all required forms are submitted"""
        app = self.applications.get(email)
        if not app:
            return False
        
        submitted_types = {f.form_type for f in app.forms_submitted}
        return submitted_types >= app.required_forms
    
    def get_application_summary(self, email: str) -> Dict:
        """Get a summary of application status"""
        app = self.applications.get(email)
        if not app:
            return {'exists': False}
        
        submitted_types = {f.form_type for f in app.forms_submitted}
        missing_forms = self.get_missing_forms(email)
        
        return {
            'exists': True,
            'applicant_name': app.applicant_name,
            'status': app.status,
            'created_at': app.created_at,
            'updated_at': app.updated_at,
            'forms_submitted_count': len(app.forms_submitted),
            'forms_required_count': len(app.required_forms),
            'is_complete': self.is_application_complete(email),
            'missing_forms': missing_forms,
            'submitted_forms': [
                {
                    'form_name': f.form_name,
                    'submitted_at': f.submitted_at
                }
                for f in app.forms_submitted
            ],
            'classification': app.classification_results
        }


# Global tracker instance
_tracker = None

def get_tracker() -> ApplicationTracker:
    """Get the global application tracker instance (singleton)"""
    global _tracker
    if _tracker is None:
        _tracker = ApplicationTracker()
    return _tracker