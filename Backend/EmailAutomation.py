"""
Email Automation - Gmail SMTP
=============================
Send emails via voice commands through Gmail SMTP.
Requires: Gmail App Password (not regular password)
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import Optional, List
from dotenv import dotenv_values

env = dotenv_values(".env")

class EmailAutomation:
    """
    Email automation using Gmail SMTP.
    
    Setup:
    1. Enable 2FA on Gmail
    2. Create App Password: Google Account → Security → App Passwords
    3. Add to .env: GMAIL_ADDRESS=your@gmail.com, GMAIL_APP_PASSWORD=xxxx
    """
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email = env.get("GMAIL_ADDRESS", "")
        self.password = env.get("GMAIL_APP_PASSWORD", "")
        
        # Draft storage
        self.pending_email = None
        
        print(f"[EMAIL] Automation loaded. Configured: {bool(self.email and self.password)}")
    
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(self.email and self.password)
    
    def draft_email(self, to: str, subject: str, body: str, 
                    cc: Optional[List[str]] = None,
                    attachments: Optional[List[str]] = None) -> dict:
        """
        Draft an email (stores for confirmation before sending).
        
        Args:
            to: Recipient email
            subject: Email subject
            body: Email body (can be plain text or HTML)
            cc: Optional CC list
            attachments: Optional list of file paths
        
        Returns:
            Draft details dict
        """
        self.pending_email = {
            "to": to,
            "subject": subject,
            "body": body,
            "cc": cc or [],
            "attachments": attachments or []
        }
        
        preview = f"""
📧 **Email Draft**
━━━━━━━━━━━━━━━━━━━━
**To:** {to}
**Subject:** {subject}
**Body Preview:** {body[:200]}{'...' if len(body) > 200 else ''}
━━━━━━━━━━━━━━━━━━━━
Say 'send it' or 'yes' to send, or 'cancel' to discard.
"""
        return {
            "success": True,
            "message": preview,
            "draft": self.pending_email
        }
    
    def send_pending(self) -> dict:
        """Send the pending/drafted email"""
        if not self.pending_email:
            return {"success": False, "message": "No email drafted. Draft one first!"}
        
        result = self._send_email(
            to=self.pending_email["to"],
            subject=self.pending_email["subject"],
            body=self.pending_email["body"],
            cc=self.pending_email.get("cc"),
            attachments=self.pending_email.get("attachments")
        )
        
        if result["success"]:
            self.pending_email = None  # Clear after sending
        
        return result
    
    def send_quick(self, to: str, subject: str, body: str) -> dict:
        """Send email immediately without drafting first"""
        return self._send_email(to, subject, body)
    
    def _send_email(self, to: str, subject: str, body: str,
                    cc: Optional[List[str]] = None,
                    attachments: Optional[List[str]] = None) -> dict:
        """Internal method to actually send the email"""
        if not self.is_configured():
            return {
                "success": False,
                "message": "Email not configured! Add GMAIL_ADDRESS and GMAIL_APP_PASSWORD to .env"
            }
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.email
            msg["To"] = to
            msg["Subject"] = subject
            
            if cc:
                msg["Cc"] = ", ".join(cc)
            
            # Attach body
            msg.attach(MIMEText(body, "plain"))
            
            # Attach files if any
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                "Content-Disposition",
                                f"attachment; filename={os.path.basename(file_path)}"
                            )
                            msg.attach(part)
            
            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                
                recipients = [to] + (cc or [])
                server.sendmail(self.email, recipients, msg.as_string())
            
            print(f"[EMAIL] ✅ Sent to {to}")
            return {
                "success": True,
                "message": f"✅ Email sent to {to}!"
            }
            
        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "message": "❌ Gmail authentication failed. Check App Password in .env"
            }
        except Exception as e:
            print(f"[EMAIL] Error: {e}")
            return {
                "success": False,
                "message": f"❌ Failed to send: {str(e)}"
            }
    
    def cancel_draft(self) -> dict:
        """Cancel pending email draft"""
        if self.pending_email:
            self.pending_email = None
            return {"success": True, "message": "📧 Email draft cancelled."}
        return {"success": False, "message": "No draft to cancel."}
    
    def has_pending(self) -> bool:
        """Check if there's a pending email"""
        return self.pending_email is not None


# Singleton instance
email_automation = EmailAutomation()


# Quick access functions
def draft_email(to: str, subject: str, body: str) -> dict:
    """Draft an email for review"""
    return email_automation.draft_email(to, subject, body)

def send_email() -> dict:
    """Send the pending email"""
    return email_automation.send_pending()

def cancel_email() -> dict:
    """Cancel draft"""
    return email_automation.cancel_draft()


if __name__ == "__main__":
    print("Email Automation Test")
    print(f"Configured: {email_automation.is_configured()}")
    
    # Test draft
    result = email_automation.draft_email(
        to="test@example.com",
        subject="Test from KAI",
        body="Hello! This is a test email from your AI assistant."
    )
    print(result["message"])
