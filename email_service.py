import os
from flask import render_template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Добавяме template_name като аргумент (ако не е подаден, ще ползва стария по подразбиране)
def send_training_email(user, link, campaign=None, open_pixel_url=None, template_name="emails/security_alert.html"):
    
    # Автоматично избираме подходящо заглавие (Subject) според избрания шаблон
    if "email_scam_1" in template_name:
        subject_text = "⚠️ КРИТИЧНО: Засечен неоторизиран опит за достъп"
    elif "email_scam_2" in template_name:
        subject_text = "⚙️ Спешно известие: Пощенската Ви кутия е запълнена на 98%"
    elif "email_scam_3" in template_name:
        subject_text = "🌳 HR: Потвърдете получаването на Вашите ваучери"
    else:
        subject_text = "Обучение по киберсигурност"

    # Заменяме статичния път с променливата template_name
    html_content = render_template(
        template_name,
        user=user,
        link=link,
        campaign=campaign,
        open_pixel_url=open_pixel_url
    )

    message = Mail(
        from_email=os.environ.get(
            "SENDGRID_FROM_EMAIL",
            "noreply.security.education@gmail.com"
        ),
        to_emails=user.email,
        subject=subject_text,  # Вече заглавието съответства на текста вътре!
        html_content=html_content
    )

    try:
        api_key = os.environ.get("SENDGRID_API_KEY")

        if not api_key:
            print("SENDGRID ERROR: missing SENDGRID_API_KEY")
            return False

        sg = SendGridAPIClient(api_key)
        response = sg.send(message)

        print("SENDGRID STATUS:", response.status_code)
        return True

    except Exception as e:
        print("SENDGRID ERROR:", e)
        return False


# Обновяваме и съвместимия alias, за да не даде грешка, ако се извика другаде
def send_phishing_email(user, link, campaign=None, open_pixel_url=None, template_name="emails/security_alert.html"):
    return send_training_email(user, link, campaign, open_pixel_url, template_name)
