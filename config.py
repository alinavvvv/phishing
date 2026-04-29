import os

class Config:
    SECRET_KEY = "your-secret-key"

    SQLALCHEMY_DATABASE_URI = "sqlite:///db.sqlite3"

    # 🔹 SendGrid / Mail settings
    MAIL_SERVER = "smtp.sendgrid.net"
    MAIL_PORT = 587
    MAIL_USE_TLS = True

    MAIL_USERNAME = "apikey"
    MAIL_PASSWORD = os.environ.get("SENDGRID_API_KEY")

    MAIL_DEFAULT_SENDER = "noreply.security.training@gmail.com"
