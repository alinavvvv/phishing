import os
from flask import render_template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_training_email(user, link, campaign=None, open_pixel_url=None):
    html_content = render_template(
        "emails/security_alert.html",
        user=user,
        link=link,
        campaign=campaign,
        open_pixel_url=open_pixel_url
    )

    message = Mail(
        from_email=os.environ.get(
            "SENDGRID_FROM_EMAIL",
            "noreply.security.training@gmail.com"
        ),
        to_emails=user.email,
        subject="Обучение по киберсигурност",
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(message)
        print("SENDGRID STATUS:", response.status_code)
        return True

    except Exception as e:
        print("SENDGRID ERROR:", e)
        return False
