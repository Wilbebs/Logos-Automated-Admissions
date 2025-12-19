import os
from simple_salesforce import Salesforce
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def diagnose_leads(email):
    print("\n" + "="*60)
    print(f"🔍 DIAGNOSING LEADS FOR: {email}")
    print("="*60)

    try:
        sf = Salesforce(
            username=os.getenv('SALESFORCE_USERNAME'),
            password=os.getenv('SALESFORCE_PASSWORD'),
            security_token=os.getenv('SALESFORCE_SECURITY_TOKEN'),
            consumer_key=os.getenv('SALESFORCE_CONSUMER_KEY'),
            consumer_secret=os.getenv('SALESFORCE_CONSUMER_SECRET'),
            domain='login'
        )
        print("✓ Connected to Salesforce")

        # Query ALL leads with this email
        query = f"SELECT Id, Name, Email, CreatedDate, Forms_Submitted_Count__c FROM Lead WHERE Email = '{email}' ORDER BY CreatedDate DESC"
        results = sf.query(query)

        print(f"\nFound {results['totalSize']} total leads for '{email}':")
        for i, rec in enumerate(results['records']):
            print(f"{i+1}. ID: {rec['Id']} | Created: {rec['CreatedDate']} | Name: {rec['Name']} | Forms: {rec.get('Forms_Submitted_Count__c')}")

        if results['totalSize'] > 1:
            print("\n⚠️ DUPLICATES DETECTED!")
            print(f"The system WILL now pick the latest ID: {results['records'][0]['Id']}")
        elif results['totalSize'] == 1:
            print("\n✅ Single lead found. No duplicates.")
        else:
            print("\nℹ️ No leads found for this email.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    email_to_check = "web@logos.edu"
    diagnose_leads(email_to_check)
