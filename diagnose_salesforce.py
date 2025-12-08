import os
import sys
import requests
from simple_salesforce import Salesforce, SalesforceLogin
import logging

import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_salesforce_connection():
    print("\n" + "="*60)
    print("🔍 SALESFORCE AUTHENTICATION DIAGNOSTIC TOOL")
    print("="*60)

    # 1. Load Credentials
    instance_url = os.getenv('SALESFORCE_INSTANCE_URL')
    consumer_key = os.getenv('SALESFORCE_CONSUMER_KEY')
    consumer_secret = os.getenv('SALESFORCE_CONSUMER_SECRET')
    username = os.getenv('SALESFORCE_USERNAME')
    password = os.getenv('SALESFORCE_PASSWORD')
    security_token = os.getenv('SALESFORCE_SECURITY_TOKEN') # New optional var

    print(f"Username: {username}")
    print(f"Consumer Key present: {'Yes' if consumer_key else 'No'}")
    print(f"Consumer Secret present: {'Yes' if consumer_secret else 'No'}")
    
    if not (username and password and consumer_key and consumer_secret):
        print("\n❌ MISSING ENVIRONMENT VARIABLES")
        print("Please ensure the following are set:")
        print("- SALESFORCE_USERNAME")
        print("- SALESFORCE_PASSWORD")
        print("- SALESFORCE_CONSUMER_KEY")
        print("- SALESFORCE_CONSUMER_SECRET")
        print("Optional: SALESFORCE_SECURITY_TOKEN, SALESFORCE_INSTANCE_URL")
        return

    # 2. Analyze Password structure
    print("\n🔐 analyzing Password structure...")
    password_len = len(password)
    print(f"Total Password Field Length: {password_len}")
    
    # Heuristic check for token concatenation
    likely_has_token = password_len > 20 # Arbitrary threshold, passwords usually <20, tokens ~25
    print(f"Likely contains concatenated token: {likely_has_token}")

    # 3. Test Method A: Standard Simple-Salesforce (Concatenated)
    print("\n[TEST A] Attempting Standard Connection (Username/Password+Token)...")
    try:
        sf = Salesforce(
            username=username,
            password=password, # As is
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            domain='login' # Default
        )
        print("✅ TEST A SUCCESS: Connected via standard login domain!")
        print(f"Session ID: {sf.session_id[:10]}...")
        return
    except Exception as e:
        print(f"❌ TEST A FAILED: {str(e)}")

    # 4. Test Method B: Split Password and Token
    print("\n[TEST B] Attempting Split Credential Connection...")
    
    # Try to extract token if not provided explicitly
    real_password = password
    real_token = security_token
    
    if not real_token and likely_has_token:
        # User might have concatenated. Ask or try to guess?
        # Let's assume the last 24-25 chars are token if explicit token is missing
        # But this is risky. Better to just warn.
        print("   >> No explicit SALESFORCE_SECURITY_TOKEN found.")
        print("   >> If you concatenated them in PASSWORD, Test A should have worked.")
    
    if real_token:
        try:
            print(f"   >> Using explicit Security Token (len={len(real_token)})")
            sf = Salesforce(
                username=username,
                password=password, # Assuming user cleaned this if they supplied token? 
                                # Or is this the raw pw? This is ambiguous in a script.
                                # Let's assume if token is provided, password should be just password.
                security_token=real_token,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                domain='login'
            )
            print("✅ TEST B SUCCESS: Connected via split credentials!")
            return
        except Exception as e:
            print(f"❌ TEST B FAILED: {str(e)}")
    else:
        print("   >> Skipping Test B (No independent security token provided)")

    # 5. Test Method C: Custom Domain
    print("\n[TEST C] Attempting Custom Domain Connection...")
    if instance_url:
        # Better extraction for My Domain
        clean_url = instance_url.replace("https://", "").replace("http://", "").rstrip('/')
        
        # If it's a "my.salesforce.com" domain, we need to be careful with simple-salesforce 'domain' arg
        # If we pass 'logosuniversity.my', simple-salesforce creates 'https://logosuniversity.my.salesforce.com'
        
        if 'my.salesforce.com' in clean_url:
             domain_part = clean_url.split('.salesforce.com')[0]
        else:
             domain_part = clean_url.split('.')[0]
             
        print(f"   >> Extracted domain arg: {domain_part}")
        
        try:
            sf = Salesforce(
                username=username,
                password=password,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                domain=domain_part 
            )
            print("✅ TEST C SUCCESS: Connected via custom domain!")
            return
        except Exception as e:
            print(f"❌ TEST C FAILED: {str(e)}")
            
            # 6. Test Method D: Raw Requests (Debug)
            print("\n[TEST D] Raw OAuth Request Analysis...")
            # specific token endpoint for My Domain
            token_url = f"https://{domain_part}.salesforce.com/services/oauth2/token"
            
            data = {
                'grant_type': 'password',
                'client_id': consumer_key,
                'client_secret': consumer_secret,
                'username': username,
                'password': password 
            }
            try:
                print(f"   >> POST {token_url}")
                response = requests.post(token_url, data=data)
                print(f"   >> Status Code: {response.status_code}")
                # Print first 500 chars of response to identify specific error
                print(f"   >> Response: {response.text[:500]}")
            except Exception as req_e:
                print(f"   >> Request failed: {req_e}")
    else:
        print("   >> Skipping Test C (No SALESFORCE_INSTANCE_URL provided)")

    print("\n" + "="*60)
    print("❌ All automated tests failed. Please review the errors above.")
    print("="*60)

if __name__ == "__main__":
    test_salesforce_connection()
