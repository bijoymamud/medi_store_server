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

def send_otp_email(email: str, otp: str, is_reset: bool = False):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        # Mock sending email fallback
        print("="*40)
        print(f"MOCK EMAIL SENDER (No SMTP credentials found in .env)")
        print(f"To: {email}")
        print(f"Subject: Mamud Health Care - {'Reset Password' if is_reset else 'Account Verification'} OTP")
        print(f"Body: Your one-time password is {otp}. It expires in 10 minutes.")
        print("="*40)
        return

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_EMAIL
        msg['To'] = email
        msg['Subject'] = f"Mamud Health Care - {'Reset Password' if is_reset else 'Account Verification'} OTP"
        
        # Plain text version for fallback
        text_body = f"Hello!\n\nYour one-time password for Mamud Health Care is: {otp}\n\nIt expires in 10 minutes."
        msg.attach(MIMEText(text_body, 'plain'))
        
        # HTML version - Bulletproof email layout using HTML table structure
        otp_boxes_td = ""
        for i, digit in enumerate(otp):
            otp_boxes_td += f'<td align="center" width="40" height="40" style="border: 1.5px solid #22BA9D; background-color: #e8f7f5; border-radius: 6px; font-family: sans-serif; font-size: 22px; font-weight: bold; color: #1a5c53; text-align: center; vertical-align: middle;">{digit}</td>'
            if i < len(otp) - 1:
                otp_boxes_td += '<td width="8"></td>'

        otp_table = f"""
        <table align="center" cellpadding="0" cellspacing="0" border="0" style="margin: 15px auto 30px auto;">
            <tr>
                {otp_boxes_td}
            </tr>
        </table>
        """

        subject_title = "Your OTP Verification Code"
        name = email.split('@')[0].capitalize()
        action_text = "reset your password" if is_reset else "verify and register your account"
        next_step_text = "You will then be prompted to set a new password." if is_reset else "This will complete your registration process."

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject_title}</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #334155; -webkit-font-smoothing: antialiased;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f1f5f9; padding: 40px 10px;">
                <tr>
                    <td align="center">
                        <table width="100%" max-width="600px" style="max-width: 500px; background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);" cellpadding="0" cellspacing="0" border="0">
                            <!-- Header -->
                            <tr>
                                <td style="background-color: #22BA9D; padding: 25px; text-align: center; border-bottom: 3px solid #1d9c83;">
                                    <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #ffffff; letter-spacing: 0.5px;">{subject_title}</h1>
                                </td>
                            </tr>
                            
                            <!-- Body -->
                            <tr>
                                <td style="padding: 40px 30px; line-height: 1.6; font-size: 15px; text-align: left;">
                                    <p style="margin: 0 0 16px 0; font-weight: 700; font-size: 17px; color: #0f172a;">Hi {name},</p>
                                    
                                    <p style="margin: 0 0 16px 0; color: #475569;">You have requested to {action_text}.</p>
                                    
                                    <p style="margin: 0 0 30px 0; color: #475569;">To ensure safety & security, please use the following OTP code to verify your identity. {next_step_text}</p>
                                    
                                    <!-- OTP Code Table -->
                                    {otp_table}
                                    
                                    <p style="margin: 0 0 20px 0; color: #475569; font-weight: 500;">Please enter this OTP within 10 minutes of receiving this email to complete your verification process.</p>
                                    
                                    <hr style="border: 0; border-top: 1px solid #f1f5f9; margin: 30px 0;">
                                    
                                    <p style="margin: 0 0 12px 0; font-size: 13px; color: #94a3b8; font-style: italic;">If you did not request this, please ignore this email or contact support at <a href="mailto:support@mamudhealthcare.com" style="color: #22BA9D; text-decoration: none;">support@mamudhealthcare.com</a></p>
                                    
                                    <p style="margin: 0 0 30px 0; font-size: 13px; color: #94a3b8;">Note: This is a system generated message. Do not reply to this email.</p>
                                    
                                    <p style="margin: 0; color: #475569;">
                                        Best Regards,<br>
                                        <strong style="color: #0f172a;">Team Mamud Health Care</strong>
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_EMAIL, email, text)
        server.quit()
        print(f"Successfully sent OTP to {email}")
    except Exception as e:
        print(f"Failed to send email to {email}: {str(e)}")
