import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_phishing_email(user, link):
    message = Mail(
        from_email=os.environ.get("MAIL_DEFAULT_SENDER"),
        to_emails=user.email,
        subject="Security Awareness Training",
        html_content=f"<a href='{link}'>Verify account</a>"
    )

    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(message)
        print("SendGrid status:", response.status_code)

    except Exception as e:
        print("EMAIL ERROR:", e)
