from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))

    company = db.Column(db.String(200))
    position = db.Column(db.String(200))

    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))

    email = db.Column(db.String(120), unique=True)

    risk_score = db.Column(db.Integer, default=0)

    clicks = db.relationship("Click", backref="user", lazy=True)


class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    template_name = db.Column(db.String(120), default="security_alert.html")
    frequency = db.Column(db.String(50), default="manual")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EmailEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"))

    token = db.Column(db.String(120), unique=True, nullable=False)

    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_status = db.Column(db.String(50), default="created")

    opened = db.Column(db.Boolean, default=False)
    opened_at = db.Column(db.DateTime)
    open_count = db.Column(db.Integer, default=0)

    clicked = db.Column(db.Boolean, default=False)
    clicked_at = db.Column(db.DateTime)
    click_count = db.Column(db.Integer, default=0)

    user = db.relationship("User", backref="email_events")
    campaign = db.relationship("Campaign", backref="email_events")


class Click(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    email_event_id = db.Column(db.Integer, db.ForeignKey("email_event.id"))

    ip = db.Column(db.String(100))
    user_agent = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="clicks")
    email_event = db.relationship("EmailEvent", backref="clicks")


class TrainingProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    email_event_id = db.Column(db.Integer, db.ForeignKey("email_event.id"))

    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)

    user = db.relationship("User", backref="training_progress")
    email_event = db.relationship("EmailEvent", backref="training_progress")
