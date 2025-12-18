import pymysql
import os
import requests
from pathlib import Path

class MachFormClient:
    def __init__(self):
        self.connection = pymysql.connect(
            host=os.getenv('MACHFORM_DB_HOST'),
            database=os.getenv('MACHFORM_DB_NAME'),
            user=os.getenv('MACHFORM_DB_USER'),
            password=os.getenv('MACHFORM_DB_PASSWORD'),
            cursorclass=pymysql.cursors.DictCursor
        )
        print(f"[MACHFORM] Connected to {os.getenv('MACHFORM_DB_HOST')}")
        
        # Session for authenticated requests
        self.session = requests.Session()
        self.authenticated = False
    
    def get_uploaded_files(self, form_id, entry_id):
        """Get file hashes for a form entry"""
        try:
            with self.connection.cursor() as cursor:
                # Query for file upload fields (element_42, etc.)
                sql = f"SELECT * FROM ap_form_{form_id} WHERE id = %s"
                cursor.execute(sql, (entry_id,))
                result = cursor.fetchone()
                
                if not result:
                    return []
                
                # Extract file fields
                files = []
                for key, value in result.items():
                    if key.startswith('element_') and value and len(str(value)) > 30:
                        # Looks like a hashed filename
                        files.append({
                            'field': key,
                            'hashed_filename': value,
                            'file_path': f"/home/zpdorvfa/public_html/forms/data/form_{form_id}/files/{value}"
                        })
                
                return files
                
        except Exception as e:
            print(f"[MACHFORM] Error getting files: {e}")
            return []

    def get_files_by_email(self, email):
        """Find all uploaded files for an applicant by email across all active forms"""
        all_files = []
        try:
            with self.connection.cursor() as cursor:
                # 1. Get all active forms
                cursor.execute("SELECT form_id, form_name FROM ap_forms WHERE form_active=1")
                forms = cursor.fetchall()
                
                for form in forms:
                    form_id = form['form_id']
                    
                    # 2. Find email field for this form
                    cursor.execute(
                        "SELECT element_id FROM ap_form_elements WHERE form_id = %s AND element_type = 'email' ORDER BY element_id ASC LIMIT 1", 
                        (form_id,)
                    )
                    email_field = cursor.fetchone()
                    
                    if not email_field:
                        continue
                        
                    email_col = f"element_{email_field['element_id']}"
                    
                    # 3. Find entries with this email
                    # Check if table exists (safety) or just try-except the query
                    try:
                        sql = f"SELECT * FROM ap_form_{form_id} WHERE {email_col} = %s"
                        cursor.execute(sql, (email,))
                        entries = cursor.fetchall()
                        
                        for entry in entries:
                            entry_files = self._extract_files_from_entry(entry, form_id)
                            all_files.extend(entry_files)
                            
                    except Exception as table_err:
                        print(f"[MACHFORM] Skipping form {form_id}: {table_err}")
                        continue
                        
            return all_files
            
        except Exception as e:
            print(f"[MACHFORM] Error searching by email: {e}")
            return []

    def _extract_files_from_entry(self, entry_data, form_id):
        """Helper to extract file paths from entry data"""
        files = []
        for key, value in entry_data.items():
            if key.startswith('element_') and value and len(str(value)) > 30:
                # Basic heuristic for hashed filenames in MachForm
                # Valid fields are usually 32+ chars (md5 hashish)
                files.append({
                    'form_id': form_id,
                    'field': key,
                    'hashed_filename': value,
                    'file_path': f"/home/zpdorvfa/public_html/forms/data/form_{form_id}/files/{value}"
                })
        return files

        return files

    def login(self):
        """Authenticate to MachForm admin"""
        try:
            login_url = "https://logoscu.com/forms/index.php"
            
            username = os.getenv('MACHFORM_ADMIN_USER')
            password = os.getenv('MACHFORM_ADMIN_PASSWORD')
            
            if not username or not password:
                print("[MACHFORM] Admin credentials not found")
                return False
            
            # GET the login page to extract CSRF token
            response = self.session.get(login_url)
            
            # Parse CSRF token from response
            import re
            csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
            
            if not csrf_match:
                print("[MACHFORM] Could not find CSRF token")
                return False
            
            csrf_token = csrf_match.group(1)
            print(f"[MACHFORM] Got CSRF token: {csrf_token[:20]}...")
            
            # POST login with correct field names
            login_data = {
                'admin_username': username,
                'admin_password': password,
                'submit': '1',
                'csrf_token': csrf_token
            }
            
            response = self.session.post(login_url, data=login_data, allow_redirects=True)
            
            print(f"[MACHFORM] Login response: {response.status_code}")
            print(f"[MACHFORM] Final URL: {response.url}")
            
            # Check if logged in
            if 'main_panel' in response.url or 'manage_forms' in response.url:
                print("[MACHFORM] ✓ Successfully authenticated!")
                self.authenticated = True
                return True
            else:
                print(f"[MACHFORM] Login failed - stayed on login page")
                return False
                
        except Exception as e:
            print(f"[MACHFORM] Login error: {e}")
            return False

    def download_file(self, hashed_filename, form_id, save_dir='/tmp/machform_files'):
        """Download a file from MachForm server using authenticated session"""
        try:
            # Login if not already authenticated
            if not self.authenticated:
                if not self.login():
                    print("[MACHFORM] Cannot download - authentication failed")
                    return None
            
            # URL to download file
            file_url = f"https://logoscu.com/forms/data/form_{form_id}/files/{hashed_filename}"
            
            # Create save directory
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            
            # Download file using session
            response = self.session.get(file_url, timeout=30)
            
            if response.status_code == 200:
                local_path = f"{save_dir}/{hashed_filename}"
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"[MACHFORM] Downloaded: {hashed_filename}")
                return local_path
            else:
                print(f"[MACHFORM] Failed to download {hashed_filename}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[MACHFORM] Error downloading file: {e}")
            return None
