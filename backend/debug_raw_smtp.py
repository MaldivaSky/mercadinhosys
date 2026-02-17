
import smtplib
import os

# Define credentials directly to test
EMAIL_ADDRESS = 'rafaelmaldivas@gmail.com'
EMAIL_PASSWORD = 'dqyxxvdflsmodlhn' # No spaces

print(f"Testing connectivity for: {EMAIL_ADDRESS}")
print(f"Password length: {len(EMAIL_PASSWORD)}")

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
