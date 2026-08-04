import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

class Config:
    # ThingsBoard Settings (Optional)
    TB_HOST = os.getenv("THINGSBOARD_HOST", "https://schnelliot.in/").rstrip("/")
    TB_USERNAME = os.getenv("THINGSBOARD_USERNAME", "").strip()
    TB_PASSWORD = os.getenv("THINGSBOARD_PASSWORD", "").strip()

    # SMTP Settings
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com").strip()
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
    _raw_pwd = os.getenv("SMTP_PASSWORD", "")
    SMTP_PASSWORD = _raw_pwd.replace(" ", "").strip() if _raw_pwd else ""
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "").strip() or SMTP_USERNAME
    
    _recipients = os.getenv("RECIPIENT_EMAILS", "")
    RECIPIENT_EMAILS = [r.strip() for r in _recipients.split(",") if r.strip()]

    EMAIL_SUBJECT_PREFIX = os.getenv("EMAIL_SUBJECT_PREFIX", "[BBMP Smart Light Ticket Report]").strip()
    DEFAULT_REPORT_PERIOD = os.getenv("DEFAULT_REPORT_PERIOD", "today").strip()
