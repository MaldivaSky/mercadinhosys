
import smtplib
import os

# Define credentials from environment variables
EMAIL_ADDRESS = os.environ.get('MAIL_USERNAME', 'seu_email@gmail.com')
EMAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or os.environ.get('EMAIL_APP_PASSWORD')

if not EMAIL_PASSWORD:
    print("❌ ERROR: EMAIL_PASSWORD or EMAIL_APP_PASSWORD not set in environment.")
    exit(1)

print(f"Testing connectivity for: {EMAIL_ADDRESS}")
# print(f"Password length: {len(EMAIL_PASSWORD)}") # Still helpful but redacted

# Test 587 (TLS)
print("\n--- Testing port 587 (STARTTLS) ---")
try:
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        # server.set_debuglevel(1) 
        print("Connecting...")
        server.ehlo()
        print("Starting TLS...")
        server.starttls()
        server.ehlo()
        print("Logging in...")
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        print("✅ SUCCESS! Login worked on port 587.")
except Exception as e:
    print(f"❌ FAILED on 587: {e}")

# Test 465 (SSL)
print("\n--- Testing port 465 (SSL) ---")
try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        # server.set_debuglevel(1)
        print("Connecting...")
        server.ehlo()
        print("Logging in...")
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        print("✅ SUCCESS! Login worked on port 465.")
except Exception as e:
    print(f"❌ FAILED on 465: {e}")
