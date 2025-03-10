# test_email.py
import requests
import json

# Sample raw email
raw_email = """From: sender@example.com
Subject: Urgent
Date: Thu, 6 Mar 2025 10:00:00 -0500
To: recipient@example.com
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"

I will make you pay for what you have done. You will regret the day you crossed me.

http://suspicious-link.com/reset
"""

# Send to API
response = requests.post(
    "http://localhost:8000/api/analyze-email", 
    json={"raw_email": raw_email}
)

# Print results
print(json.dumps(response.json(), indent=2))