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

    def download_file(self, hashed_filename, form_id, save_dir='/tmp/machform_files'):
        """Download a file from MachForm server"""
        try:
            # URL to download file - assuming standard MachForm data structure accessible via web
            # NOTE: This assumes files are publicly accessible or this server IP is whitelisted
            file_url = f"https://logoscu.com/forms/data/form_{form_id}/files/{hashed_filename}"
            
            # Create save directory
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            
            # Download file
            response = requests.get(file_url, timeout=30)
            
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
