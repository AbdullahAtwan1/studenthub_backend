import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from app.core.config import settings

def send_email(to_email: str, subject: str, body: str):
    try:
        print("\n=== EMAIL DEBUG START ===")
        print(f"To: {to_email}")
        print(f"From: {settings.EMAIL_USER}")
        print(f"SMTP Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        print("==========================")

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = formataddr(("StudentHub", settings.EMAIL_FROM))
        msg["To"] = to_email

        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.set_debuglevel(1)
            server.starttls()
            server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
            server.sendmail(settings.EMAIL_USER, [to_email], msg.as_string())

        print("[✅] Email sent successfully!")
        print("=== EMAIL DEBUG END ===\n")

    except Exception as e:
        print(f"[❌] Email sending failed: {e}")
        print("=== EMAIL DEBUG END ===\n")
