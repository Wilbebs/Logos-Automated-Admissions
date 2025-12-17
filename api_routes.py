from flask import jsonify, request
from datetime import datetime, timedelta
import salesforce_client

def register_api_routes(app, sf_client):
    """Register API routes for frontend dashboard"""
    
    @app.route('/api/stats', methods=['GET'])
    def get_stats():
        """Get dashboard statistics"""
        try:
            # Get all leads
            all_leads = sf_client.sf.query("""
                SELECT Id, Forms_Submitted_Count__c, Forms_Complete__c, CreatedDate
                FROM Lead
                WHERE Email != NULL
            """)
            
            total = all_leads['totalSize']
            
            # Count this month
            first_of_month = datetime.now().replace(day=1).strftime('%Y-%m-%dT00:00:00Z')
            this_month = sf_client.sf.query(f"""
                SELECT COUNT(Id) cnt
                FROM Lead
                WHERE CreatedDate >= {first_of_month}
            """)['records'][0]['cnt']
            
            # Pending classification (3 forms but no classification)
            pending = sf_client.sf.query("""
                SELECT COUNT(Id) cnt
                FROM Lead
                WHERE Forms_Complete__c = true
                AND Id NOT IN (SELECT Lead__c FROM Classification__c)
            """)['records'][0]['cnt']
            
            # Classified count
            classified = sf_client.sf.query("""
                SELECT COUNT(Id) cnt
                FROM Classification__c
            """)['records'][0]['cnt']
            
            # Status breakdown
            incomplete = total - (pending + classified)
            
            # Level distribution
            level_query = sf_client.sf.query("""
                SELECT Recommended_Level__c, COUNT(Id) cnt
                FROM Classification__c
                GROUP BY Recommended_Level__c
            """)
            
            level_distribution = {
                record['Recommended_Level__c']: record['cnt'] 
                for record in level_query['records']
            }
            
            return jsonify({
                'total_applicants': total,
                'applicants_this_month': this_month,
                'pending_classification': pending,
                'classified_count': classified,
                'status_breakdown': {
                    'incomplete': incomplete,
                    'pending': pending,
                    'classified': classified
                },
                'level_distribution': level_distribution
            })
            
        except Exception as e:
            print(f"[API] Error getting stats: {e}")
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/api/applicants', methods=['GET'])
    def get_applicants():
        """Get all applicants with filters"""
        try:
            # Get query parameters
            search = request.args.get('search', '')
            status = request.args.get('status', 'all')
            level = request.args.get('level', 'all')
            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 20))
            
            # Build SOQL query - SIMPLIFIED
            where_clauses = ["Email != NULL"]
            
            if search:
                search_safe = search.replace("'", "\\'")
                where_clauses.append(f"(FirstName LIKE '%{search_safe}%' OR LastName LIKE '%{search_safe}%' OR Email LIKE '%{search_safe}%')")
            
            where_clause = " AND ".join(where_clauses)
            
            # Get total count
            count_query = f"SELECT COUNT(Id) cnt FROM Lead WHERE {where_clause}"
            total = sf_client.sf.query(count_query)['records'][0]['cnt']
            
            # Get paginated results - WITHOUT subquery
            offset = (page - 1) * limit
            query = f"""
                SELECT Id, FirstName, LastName, Email, Phone,
                       Forms_Submitted_Count__c, Forms_Complete__c,
                       Last_Form_Received__c, CreatedDate
                FROM Lead
                WHERE {where_clause}
                ORDER BY Last_Form_Received__c DESC NULLS LAST
                LIMIT {limit} OFFSET {offset}
            """
            
            results = sf_client.sf.query(query)
            
            # Get all Lead IDs to query classifications separately
            lead_ids = [r['Id'] for r in results['records']]
            
            # Query classifications separately
            classifications = {}
            if lead_ids:
                ids_str = "','".join(lead_ids)
                class_query = sf_client.sf.query(f"""
                    SELECT Lead__c, Recommended_Level__c
                    FROM Classification__c
                    WHERE Lead__c IN ('{ids_str}')
                """)
                
                for c in class_query['records']:
                    classifications[c['Lead__c']] = c.get('Recommended_Level__c')
            
            # Format applicants
            applicants = []
            for record in results['records']:
                lead_id = record['Id']
                forms_count = record.get('Forms_Submitted_Count__c') or 0
                forms_complete = record.get('Forms_Complete__c', False)
                has_classification = lead_id in classifications
                
                # Determine status
                if forms_count < 3:
                    app_status = 'incomplete'
                elif forms_complete and not has_classification:
                    app_status = 'pending'
                else:
                    app_status = 'classified'
                
                applicants.append({
                    'id': lead_id,
                    'first_name': record.get('FirstName') or '',
                    'last_name': record.get('LastName') or '',
                    'email': record.get('Email') or '',
                    'forms_submitted': int(forms_count),
                    'status': app_status,
                    'recommended_level': classifications.get(lead_id),
                    'last_activity': record.get('Last_Form_Received__c') or record.get('CreatedDate')
                })
            
            # Filter by status/level if specified
            if status != 'all':
                applicants = [a for a in applicants if a['status'] == status]
            
            if level != 'all':
                applicants = [a for a in applicants if a.get('recommended_level') == level]
            
            return jsonify({
                'applicants': applicants,
                'total': len(applicants),
                'page': page,
                'total_pages': (len(applicants) + limit - 1) // limit
            })
            
        except Exception as e:
            import traceback
            print(f"[API] Error getting applicants: {e}")
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/api/applicants/<lead_id>', methods=['GET'])
    def get_applicant_detail(lead_id):
        """Get detailed information for one applicant"""
        try:
            # Get Lead info
            lead = sf_client.sf.Lead.get(lead_id)
            
            # Get form submissions
            submissions_query = sf_client.sf.query(f"""
                SELECT Id, Form_Type__c, Submission_Date__c, Form_Data__c
                FROM Form_Submission__c
                WHERE Lead__c = '{lead_id}'
                ORDER BY Submission_Date__c ASC
            """)
            
            forms = []
            for sub in submissions_query['records']:
                import json
                form_data = json.loads(sub.get('Form_Data__c', '{}'))
                
                forms.append({
                    'form_type': sub['Form_Type__c'],
                    'submission_date': sub['Submission_Date__c'],
                    'data': form_data,
                    'files': []  # TODO: Add file handling later
                })
            
            # Get classification
            classification = None
            class_query = sf_client.sf.query(f"""
                SELECT Recommended_Level__c, Recommended_Programs__c,
                       Justification__c, Confidence_Score__c,
                       Classification_Date__c
                FROM Classification__c
                WHERE Lead__c = '{lead_id}'
                ORDER BY Classification_Date__c DESC
                LIMIT 1
            """)
            
            if class_query['totalSize'] > 0:
                c = class_query['records'][0]
                classification = {
                    'level': c.get('Recommended_Level__c'),
                    'confidence': c.get('Confidence_Score__c'),
                    'programs': c.get('Recommended_Programs__c', '').split(';') if c.get('Recommended_Programs__c') else [],
                    'justification': c.get('Justification__c'),
                    'date': c.get('Classification_Date__c')
                }
            
            # Email history placeholder (we don't store this yet)
            email_history = []
            
            return jsonify({
                'applicant': {
                    'id': lead['Id'],
                    'name': f"{lead.get('FirstName', '')} {lead.get('LastName', '')}".strip(),
                    'email': lead.get('Email'),
                    'phone': lead.get('Phone'),
                    'status': 'classified' if classification else ('pending' if lead.get('Forms_Complete__c') else 'incomplete'),
                    'forms': forms,
                    'classification': classification,
                    'email_history': email_history
                }
            })
            
        except Exception as e:
            print(f"[API] Error getting applicant detail: {e}")
            return jsonify({'error': str(e)}), 500
