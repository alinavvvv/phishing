from flask_mail import Message

def send_phishing_email(mail, user, link):
    html = f"""
    <div style="font-family:Arial;background:#f8fafc;padding:20px;">
        <div style="max-width:600px;margin:auto;background:white;padding:30px;border-radius:10px;">

            <h2 style="color:#dc2626;">⚠ Security Alert</h2>

            <p>We detected unusual login activity on your account.</p>

            <p>Please verify your account immediately to avoid suspension.</p>

            <a href="{link}"
               style="display:inline-block;margin-top:15px;
               background:#2563eb;color:white;padding:12px 20px;
               text-decoration:none;border-radius:6px;">
               Verify Account
            </a>

            <hr>
            <small>Security Awareness Training System</small>
        </div>
    </div>
    """

    msg = Message(
        subject="⚠ Security Awareness Training",
        recipients=[user.email],
        html=html
    )

    mail.send(msg)
