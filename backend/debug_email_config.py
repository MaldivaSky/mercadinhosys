
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
# The file is in backend/app/utils/email_service.py
# So if we run from backend/ we can import app.utils.email_service
from app.utils.email_service import _resolve_mail_setting

app = Flask(__name__)

with app.app_context():
    print(f"CWD: {os.getcwd()}")
    print("-" * 20)
    
    server = _resolve_mail_setting("MAIL_SERVER")
    port = _resolve_mail_setting("MAIL_PORT")
    user = _resolve_mail_setting("MAIL_USERNAME")
    password = _resolve_mail_setting("MAIL_PASSWORD")
    
    print(f"MAIL_SERVER: {str(server)}")
    print(f"MAIL_PORT: {str(port)}")
    print(f"MAIL_USERNAME: {str(user)}")
    
    if password:
        print(f"MAIL_PASSWORD found. Length: {len(password)}")
        # Mask password for security
        masked = password[:2] + "*" * (len(password)-4) + password[-2:] if len(password) > 4 else "***"
        print(f"MAIL_PASSWORD masked: {masked}")
    else:
        print("MAIL_PASSWORD: None")
    
    print("-" * 20)
