import requests
import os

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

def send_phishing_email(user, link):
    url = "https://api.sendgrid.com/v3/mail/send"

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "personalizations": [{
            "to": [{"email": user.email}]
        }],
        "from": {"email": os.environ.get("MAIL_DEFAULT_SENDER")},
        "subject": "Security Awareness Training",
        "content": [{
            "type": "text/html",
            "value": f"<a href='{link}'>Verify account</a>"
        }]
    }

    r = requests.post(url, json=data, headers=headers)
    print("SENDGRID STATUS:", r.status_code, r.text)
