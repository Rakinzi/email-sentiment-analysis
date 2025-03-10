# smtp_relay_server.py
from aiosmtpd.controller import Controller
import asyncio
import requests
import email
from email.message import EmailMessage
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

# Gmail credentials for sending
GMAIL_USER = os.getenv("GMAIL_EMAIL")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

class ThreatFilteringHandler:
    async def handle_DATA(self, server, session, envelope):
        # Get the message content
        message_data = envelope.content.decode('utf8', errors='replace')
        message = email.message_from_string(message_data)
        
        # Get message parts
        subject = message.get("Subject", "")
        from_address = envelope.mail_from
        to_addresses = envelope.rcpt_tos
        
        # Extract body
        body = ""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        part_body = part.get_payload(decode=True)
                        if part_body:
                            body += part_body.decode('utf8', errors='replace')
                    except:
                        continue
        else:
            try:
                payload = message.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf8', errors='replace')
            except:
                body = message.get_payload()
        
        # Analyze for threats
        print(f"Analyzing email: From={from_address}, To={to_addresses}, Subject={subject}")
        
        content_to_analyze = f"From: {from_address}\nTo: {', '.join(to_addresses)}\nSubject: {subject}\n\n{body}"
        
        # Call your threat detection API
        try:
            response = requests.post(
                "http://localhost:8000/api/quick-analyze",
                json={"content": content_to_analyze}
            )
            result = response.json()
            
            should_block = result.get("should_block", False)
            threat_level = result.get("threat_level", "Unknown")
            primary_harm_type = result.get("primary_harm_type", "Unknown")
            
            print(f"Analysis complete: Block={should_block}, Level={threat_level}, Type={primary_harm_type}")
            
            # Log the attempt to database via API
            log_data = {
                "sender": from_address,
                "recipient": ", ".join(to_addresses),
                "subject": subject,
                "content": body,
                "threat_level": threat_level,
                "primary_harm_type": primary_harm_type,
                "was_blocked": should_block
            }
            
            try:
                requests.post("http://localhost:8000/api/log-email-attempt", json=log_data)
            except Exception as e:
                print(f"Error logging attempt: {e}")
            
            if should_block:
                print(f"BLOCKED: Email from {from_address} contained harmful content ({primary_harm_type})")
                return "550 Email rejected due to harmful content detection"
            
            # Email is safe, forward it through Gmail
            try:
                # Create a new message
                forwarded_message = EmailMessage()
                forwarded_message["From"] = from_address
                forwarded_message["To"] = ", ".join(to_addresses)
                forwarded_message["Subject"] = subject
                forwarded_message.set_content(body)
                
                # Connect to Gmail and send
                with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                    smtp.starttls()
                    smtp.login(GMAIL_USER, GMAIL_PASSWORD)
                    smtp.send_message(forwarded_message)
                
                print(f"Email forwarded successfully to {to_addresses}")
                return "250 Message accepted for delivery"
                
            except Exception as e:
                print(f"Error forwarding email: {e}")
                return f"554 Transaction failed: {str(e)}"
                
        except Exception as e:
            print(f"Error analyzing email: {e}")
            # In case of error, default to allowing the email
            return "250 Message accepted for delivery (analysis error)"

# Run the server
if __name__ == "__main__":
    handler = ThreatFilteringHandler()
    controller = Controller(handler, hostname="127.0.0.1", port=1025)    
    print("Starting SMTP filtering relay on port 1025")
    controller.start()
    
    # Keep the server running
    try:
        print("SMTP relay server running")
        loop = asyncio.get_event_loop()
        loop.run_forever()
    except KeyboardInterrupt:
        controller.stop()
        print("SMTP relay server stopped")