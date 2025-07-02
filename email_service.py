
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
try:
    import sendgrid
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

class EmailService:
    def __init__(self):
        self.mailchimp_api_key = os.getenv('MAILCHIMP_API_KEY', '')
        self.mailchimp_server = os.getenv('MAILCHIMP_SERVER', '')  # e.g., 'us1'
        self.mailchimp_list_id = os.getenv('MAILCHIMP_LIST_ID', '')
        
        # SendGrid settings (preferred for production)
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY', '')
        self.sendgrid_from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@yourapp.com')
        
        # SMTP settings for fallback
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')

    def add_to_mailchimp(self, email, name, user_data):
        """Add user to Mailchimp list"""
        if not self.mailchimp_api_key:
            print("Mailchimp API key not configured")
            return False

        url = f"https://{self.mailchimp_server}.api.mailchimp.com/3.0/lists/{self.mailchimp_list_id}/members"
        
        data = {
            "email_address": email,
            "status": "subscribed",
            "merge_fields": {
                "FNAME": name.split()[0] if name else "",
                "LNAME": " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
                "GOAL": user_data.get('profile_data', {}).get('goal', ''),
                "SIGNUPDATE": user_data.get('created_at', '')
            }
        }

        headers = {
            "Authorization": f"Bearer {self.mailchimp_api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            return response.status_code == 200
        except Exception as e:
            print(f"Mailchimp error: {e}")
            return False

    def _send_with_sendgrid(self, to_email, subject, html_content):
        """Send email using SendGrid API"""
        if not self.sendgrid_api_key or not SENDGRID_AVAILABLE:
            return False
        
        try:
            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
            message = Mail(
                from_email=self.sendgrid_from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            response = sg.send(message)
            return response.status_code == 202
        except Exception as e:
            print(f"SendGrid error: {e}")
            return False

    def send_welcome_email(self, email, name):
        """Send welcome email to new user"""

        html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); padding: 30px; text-align: center;">
                    <h1 style="color: #3B7A57; margin: 0;">Welcome, {name}! 🎉</h1>
                </div>
                
                <div style="padding: 30px; background: white;">
                    <p>Thank you for joining our fitness companion app! You've just taken the first step toward understanding your body and achieving your goals.</p>
                    
                    <h3 style="color: #3B7A57;">What's Next?</h3>
                    <ul>
                        <li>✅ Complete your daily check-ins</li>
                        <li>🤖 Get personalized AI insights</li>
                        <li>📊 Track your progress patterns</li>
                        <li>💪 Build sustainable habits</li>
                    </ul>
                    
                    <p style="background: #f8fffe; padding: 15px; border-left: 4px solid #A8E6CF; margin: 20px 0;">
                        <strong>💡 Pro Tip:</strong> Consistency beats perfection! Even logging incomplete data helps our AI understand your patterns better.
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://your-app-url.replit.app/dashboard?email={email}" 
                           style="background: #3B7A57; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                            Start Your Journey
                        </a>
                    </div>
                    
                    <p style="color: #666; font-size: 14px;">
                        Need help? Reply to this email - we're here to support you! 💚
                    </p>
                </div>
            </body>
            </html>
            """

        # Try SendGrid first, fallback to SMTP
        if self._send_with_sendgrid(email, "Welcome to Your Fitness Journey! 🌟", html_body):
            return True
        
        # Fallback to SMTP
        if not self.smtp_username:
            print("No email service configured")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Welcome to Your Fitness Journey! 🌟"
            msg['From'] = self.smtp_username
            msg['To'] = email
            msg.attach(MIMEText(html_body, 'html'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Email sending error: {e}")
            return False

    def send_password_reset_email(self, email, name, reset_link):
        """Send password reset email"""
        if not self.smtp_username:
            print("SMTP not configured")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Password Reset Request - Fitness Companion 🔐"
            msg['From'] = self.smtp_username
            msg['To'] = email

            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); padding: 30px; text-align: center;">
                    <h1 style="color: #3B7A57; margin: 0;">Password Reset Request 🔐</h1>
                </div>
                
                <div style="padding: 30px; background: white;">
                    <p>Hi {name},</p>
                    <p>We received a request to reset your password for your Fitness Companion account.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" 
                           style="background: #3B7A57; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                            🔄 Reset Your Password
                        </a>
                    </div>
                    
                    <p style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffd93d; margin: 20px 0;">
                        <strong>⏰ Important:</strong> This link expires in 1 hour for your security.
                    </p>
                    
                    <p style="color: #666; font-size: 14px;">
                        If you didn't request this password reset, you can safely ignore this email. 
                        Your password will remain unchanged.
                    </p>
                    
                    <p style="color: #666; font-size: 14px;">
                        If the button doesn't work, copy and paste this link into your browser:<br>
                        <a href="{reset_link}" style="color: #3B7A57;">{reset_link}</a>
                    </p>
                    
                    <p style="color: #666; font-size: 14px;">
                        Need help? Reply to this email - we're here to support you! 💚
                    </p>
                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_body, 'html'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Password reset email error: {e}")
            return False

email_service = EmailService()
