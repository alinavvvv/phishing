import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///local.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SENDGRID SMTP
    MAIL_SERVER = "smtp.sendgrid.net"
    MAIL_PORT = 587
    MAIL_USE_TLS = True

    MAIL_USERNAME = "apikey"
    MAIL_PASSWORD = os.environ.get("SENDGRID_API_KEY")

    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")
