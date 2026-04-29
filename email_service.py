from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_phishing_email(user, link):
    message = Mail(
        from_email='your_email@example.com',
        to_emails=user.email,
        subject='⚠ Security Alert',
        html_content=f'''
        <h2>Security Alert</h2>
        <p>Suspicious activity detected.</p>
        <a href="{link}">Verify Account</a>
        '''
    )

    try:
        sg = SendGridAPIClient()
        sg.send(message)
        print("Email sent!")
    except Exception as e:
        print("Error:", e)
