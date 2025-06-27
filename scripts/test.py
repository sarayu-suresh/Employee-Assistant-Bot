from email_utils import fetch_recent_emails

emails = fetch_recent_emails()
for e in emails:
    print(f"📧 {e['subject']} - {e['from']}")
    print(f"   {e['snippet']}\n")