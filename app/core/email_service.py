import smtplib
from email.message import EmailMessage
from app.core.config import settings

def send_otp_email(to_email: str, otp: str):
    msg = EmailMessage()
    msg["Subject"] = "StudentHub OTP Verification"
    msg["From"] = settings.GMAIL_USER
    msg["To"] = to_email
    msg.set_content(f"Your StudentHub OTP code is {otp}. It will expire in 10 minutes.")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(settings.GMAIL_USER, settings.GMAIL_APP_PASSWORD)
        smtp.send_message(msg)
