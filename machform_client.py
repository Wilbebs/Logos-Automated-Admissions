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
        entry_id = entry_data.get('id')  # Get entry ID
        
        for key, value in entry_data.items():
            if key.startswith('element_') and value:
                value_str = str(value)
                # Filter for actual files
                if (len(value_str) > 50 and 
                    '_' in value_str and 
                    not value_str.startswith('http') and
                    '@' not in value_str and
                    ('|' in value_str or '.pdf' in value_str.lower() or '.doc' in value_str.lower())):
                    
                    files.append({
                        'form_id': form_id,
                        'entry_id': entry_id,  # Add this
                        'field': key,
                        'hashed_filename': value_str
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

    def get_download_links_from_entry(self, form_id, entry_id):
        """Parse download links from entry view page"""
        try:
            if not self.authenticated:
                if not self.login():
                    return []
            
            entry_url = f"https://logoscu.com/forms/view_entry.php?form_id={form_id}&entry_id={entry_id}"
            response = self.session.get(entry_url)
            
            if response.status_code != 200:
                print(f"[MACHFORM] Failed to load entry page: {response.status_code}")
                return []
            
            import re
            
            # Robust pattern: handles absolute/relative URLs and captures filename
            # This covers: href="download.php?q=..." OR href="https://logoscu.com/forms/download.php?q=..."
            pattern = r'href="([^"]*download\.php\?q=[^"]+)"[^>]*>(.*?)</a>'
            matches = re.findall(pattern, response.text)
            
            links = []
            
            if matches:
                for url, filename in matches:
                    # Clean filename (strip HTML tags if any, though unlikely)
                    clean_filename = re.sub(r'<[^>]+>', '', filename).strip()
                    
                    # Ensure full URL
                    if not url.startswith('http'):
                        if url.startswith('/'):
                            url = f"https://logoscu.com{url}"
                        else:
                            url = f"https://logoscu.com/forms/{url}"
                    
                    # If filename is empty or too long (regex quirk), generate a generic one
                    # but usually link text contains the actual filename with extension
                    if not clean_filename or len(clean_filename) > 200:
                        clean_filename = f"form_{form_id}_entry_{entry_id}_file_{len(links)+1}"
                    
                    links.append({'url': url, 'filename': clean_filename})
                    print(f"[MACHFORM] Found download: {clean_filename[:40]}")
            else:
                print(f"[MACHFORM] No download links found in entry {entry_id}")
            
            return links
            
        except Exception as e:
            print(f"[MACHFORM] Error parsing entry: {e}")
            return []

    def download_file_from_link(self, download_url, filename, save_dir='/tmp/machform_files'):
        """Download file using authenticated download.php link"""
        try:
            if not self.authenticated:
                if not self.login():
                    return None
            
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            
            response = self.session.get(download_url, timeout=30)
            
            if response.status_code == 200:
                # Clean filename
                safe_filename = filename.replace('/', '_').replace('\\', '_')
                local_path = f"{save_dir}/{safe_filename}"
                
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"[MACHFORM] ✓ Downloaded: {safe_filename[:50]}")
                return local_path
            else:
                print(f"[MACHFORM] Download failed {filename[:30]}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[MACHFORM] Download error: {e}")
            return None
