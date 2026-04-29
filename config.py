import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")

    DATABASE_URL = os.environ.get("DATABASE_URL")

    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or "sqlite:///local.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MAIL
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_USERNAME")
