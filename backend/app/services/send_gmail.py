# app/services/send_gmail.py
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_via_gmail(sender_email, recipient_email, subject, message_body, app_password=None):
    """
    Send an email via Gmail SMTP server
    
    Args:
        sender_email (str): Email address of the sender
        recipient_email (str): Email address of the recipient
        subject (str): Email subject
        message_body (str): Content of the email
        app_password (str): App password for Gmail account (optional)
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Use provided app_password or get from environment
        gmail_password = app_password or os.environ.get("GMAIL_APP_PASSWORD")
        
        if not gmail_password:
            print("Error: Gmail app password not configured")
            return False
            
        # Set up the MIME
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(message_body, 'plain'))
        
        # Setup the SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure the connection
        
        # Login to server
        server.login(sender_email, gmail_password)
        
        # Send email
        server.send_message(msg)
        
        # Terminate the session
        server.quit()
        
        return True
    
    except Exception as e:
        print(f"Error sending email: {e}")
        return False