import smtplib
from email.message import EmailMessage
from app.core.config import settings


def send_otp_email(to_email: str, otp: str):
    msg = EmailMessage()
    msg["Subject"] = "StudentHub OTP Verification"
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg.set_content(
        f"Your StudentHub OTP code is {otp}. It will expire in {settings.OTP_TTL_MINUTES} minutes."
    )

    with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as smtp:
        smtp.starttls()
        smtp.login(settings.EMAIL_USER, settings.EMAIL_PASS)
        smtp.send_message(msg)
