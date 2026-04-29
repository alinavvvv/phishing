import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_phishing_email(user, link):
    message = Mail(
        from_email="noreply.security.training@gmail.com",
        to_emails=user.email,
        subject="Security Training Alert",
        html_content=f"""
        <h3>Security Awareness Training</h3>
        <p>Click the link to verify login attempt:</p>
        <a href="{link}">Verify</a>
        """
    )

    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(message)
        print("STATUS:", response.status_code)

    except Exception as e:
        print("SENDGRID ERROR:", e)
        raise e
