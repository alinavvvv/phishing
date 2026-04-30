import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # DATABASE
    uri = os.environ.get("DATABASE_URL")

    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = uri or "sqlite:///db.sqlite3"

    # SendGrid API key
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
