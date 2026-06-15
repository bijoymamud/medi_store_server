import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def generate_otp() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(6))

def send_otp_email(email: str, otp: str):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        # Mock sending email fallback
        print("="*40)
        print(f"MOCK EMAIL SENDER (No SMTP credentials found in .env)")
        print(f"To: {email}")
        print(f"Subject: Your Verification OTP")
        print(f"Body: Your one-time password is {otp}. It expires in 10 minutes.")
        print("="*40)
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = email
        msg['Subject'] = "MediShop - Your Verification OTP"
        
        body = f"Hello!\n\nYour one-time password for MediShop is: {otp}\n\nIt expires in 10 minutes."
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_EMAIL, email, text)
        server.quit()
        print(f"Successfully sent OTP to {email}")
    except Exception as e:
        print(f"Failed to send email to {email}: {str(e)}")
