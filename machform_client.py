import pymysql
import os

class MachFormClient:
    def __init__(self):
        self.connection = pymysql.connect(
            host=os.getenv('MACHFORM_DB_HOST', 'localhost'),
            database=os.getenv('MACHFORM_DB_NAME'),
            user=os.getenv('MACHFORM_DB_USER'),
            password=os.getenv('MACHFORM_DB_PASSWORD'),
            cursorclass=pymysql.cursors.DictCursor
        )
    
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
