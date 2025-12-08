"""
Salesforce Client - Handles all Salesforce API interactions
"""
import os
from simple_salesforce import Salesforce
from datetime import datetime

class SalesforceClient:
    def __init__(self):
        """Initialize Salesforce connection"""
        self.instance_url = os.getenv('SALESFORCE_INSTANCE_URL')
        self.consumer_key = os.getenv('SALESFORCE_CONSUMER_KEY')
        self.consumer_secret = os.getenv('SALESFORCE_CONSUMER_SECRET')
        self.username = os.getenv('SALESFORCE_USERNAME')
        self.password = os.getenv('SALESFORCE_PASSWORD')
        self.security_token = os.getenv('SALESFORCE_SECURITY_TOKEN')
        
        self.sf = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Salesforce"""
        try:
            print(f"[SALESFORCE DEBUG] Username: {self.username}")
            print(f"[SALESFORCE DEBUG] Password length: {len(self.password) if self.password else 0}")
            print(f"[SALESFORCE DEBUG] Security Token: {'Yes' if self.security_token else 'No (External)'}")
            
            # Use explicit token parameter if available (FIX for invalid_grant)
            self.sf = Salesforce(
                username=self.username,
                password=self.password,
                security_token=self.security_token,
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret,
                domain='login' 
            )
            print("[SALESFORCE] ✓ Connected successfully")
        except Exception as e:
            print(f"[SALESFORCE] ❌ Connection failed: {e}")
            self.sf = None
    
    def find_or_create_lead(self, email, first_name, last_name):
        """Find existing Lead by email or create new one"""
        if not self.sf:
            return None
        
        try:
            # Search for existing Lead
            query = f"SELECT Id, Email, FirstName, LastName FROM Lead WHERE Email = '{email}' LIMIT 1"
            results = self.sf.query(query)
            
            if results['totalSize'] > 0:
                lead_id = results['records'][0]['Id']
                print(f"[SALESFORCE] Found existing Lead: {lead_id}")
                return lead_id
            
            # Create new Lead
            lead_data = {
                'FirstName': first_name,
                'LastName': last_name,
                'Email': email,
                'Company': 'UCL Applicant',
                'Status': 'Open - Not Contacted'
            }
            
            result = self.sf.Lead.create(lead_data)
            lead_id = result['id']
            print(f"[SALESFORCE] Created new Lead: {lead_id}")
            return lead_id
            
        except Exception as e:
            print(f"[SALESFORCE] Error with Lead: {e}")
            return None
    
    def create_form_submission(self, lead_id, form_type, form_data_json):
        """Create Form_Submission__c record"""
        if not self.sf or not lead_id:
            return None
        
        try:
            submission_data = {
                'Lead__c': lead_id,
                'Form_Type__c': form_type,
                'Form_Data_JSON__c': form_data_json[:131072],  # Respect field length
                'Submission_Date__c': datetime.utcnow().isoformat(),
                'Status__c': 'Received'
            }
            
            result = self.sf.Form_Submission__c.create(submission_data)
            submission_id = result['id']
            print(f"[SALESFORCE] Created Form_Submission: {submission_id}")
            return submission_id
            
        except Exception as e:
            print(f"[SALESFORCE] Error creating Form_Submission: {e}")
            return None
    
    def update_lead_form_count(self, lead_id):
        """Update Lead's form count and check if complete"""
        if not self.sf or not lead_id:
            return
        
        try:
            # Count form submissions for this Lead
            query = f"SELECT COUNT() FROM Form_Submission__c WHERE Lead__c = '{lead_id}'"
            result = self.sf.query(query)
            count = result['totalSize']
            
            # Update Lead
            update_data = {
                'Forms_Submitted_Count__c': count,
                'Forms_Complete__c': count >= 3,
                'Last_Form_Received__c': datetime.utcnow().isoformat()
            }
            
            self.sf.Lead.update(lead_id, update_data)
            print(f"[SALESFORCE] Updated Lead form count: {count}/3")
            
            return count >= 3
            
        except Exception as e:
            print(f"[SALESFORCE] Error updating Lead: {e}")
            return False
    
    def create_classification(self, lead_id, classification_data, status='Preliminary'):
        """Create Classification__c record"""
        if not self.sf or not lead_id:
            return None
        
        try:
            import json
            
            classification_record = {
                'Lead__c': lead_id,
                'Recommended_Level__c': classification_data.get('recommended_level', '')[:100],
                'Recommended_Programs__c': '\n'.join(classification_data.get('recommended_programs', []))[:32768],
                'Confidence_Score__c': classification_data.get('confidence_score', 0),
                'Classification_Date__c': datetime.utcnow().isoformat(),
                'Gemini_Response_JSON__c': json.dumps(classification_data, ensure_ascii=False)[:131072],
                'Status__c': status
            }
            
            result = self.sf.Classification__c.create(classification_record)
            classification_id = result['id']
            print(f"[SALESFORCE] Created Classification ({status}): {classification_id}")
            return classification_id
            
        except Exception as e:
            print(f"[SALESFORCE] Error creating Classification: {e}")
            return None
    
    def get_all_form_submissions(self, lead_id):
        """Get all form submissions for a Lead"""
        if not self.sf or not lead_id:
            return []
        
        try:
            query = f"""
                SELECT Form_Type__c, Form_Data_JSON__c, Submission_Date__c 
                FROM Form_Submission__c 
                WHERE Lead__c = '{lead_id}'
                ORDER BY Submission_Date__c ASC
            """
            results = self.sf.query(query)
            return results['records']
            
        except Exception as e:
            print(f"[SALESFORCE] Error fetching submissions: {e}")
            return []