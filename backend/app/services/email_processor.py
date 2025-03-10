import email
from email.header import decode_header
import re
from typing import Dict, Any

def parse_email_content(raw_email: str) -> Dict[str, Any]:
    """
    Parse raw email content and extract relevant information
    
    Args:
        raw_email (str): Raw email content including headers and body
        
    Returns:
        dict: Extracted email components
    """
    # Parse the email
    msg = email.message_from_string(raw_email)
    
    # Extract subject
    subject = msg["Subject"]
    if subject:
        subject, encoding = decode_header(subject)[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")
    
    # Extract sender
    from_address = msg["From"]
    
    # Extract body
    body = ""
    if msg.is_multipart():
        # Handle multipart emails
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Skip attachments
            if "attachment" in content_disposition:
                continue
            
            # Get text content
            if content_type == "text/plain" or content_type == "text/html":
                try:
                    body_part = part.get_payload(decode=True).decode()
                    body += body_part
                except:
                    pass
    else:
        # Handle plain text emails
        body = msg.get_payload(decode=True).decode()
    
    # Clean HTML if present
    if body.startswith("<html") or "<body" in body:
        body = re.sub(r'<[^>]+>', ' ', body)
    
    return {
        "subject": subject,
        "from": from_address,
        "body": body,
        "full_content": f"Subject: {subject}\nFrom: {from_address}\n\n{body}"
    }