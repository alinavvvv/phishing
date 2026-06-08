from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))

    company = db.Column(db.String(200))
    position = db.Column(db.String(200))

    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))

    email = db.Column(db.String(120), unique=True)

    risk_score = db.Column(db.Integer, default=0)

    # Връзки, сочещи към другите модели чрез back_populates
    clicks = db.relationship("Click", back_populates="user", lazy=True)
    email_events = db.relationship("EmailEvent", back_populates="user", lazy=True)
    training_progress = db.relationship("TrainingProgress", back_populates="user", lazy=True)

    def click_rate(self):
        sent_count = EmailEvent.query.filter_by(user_id=self.id).count()
        if sent_count == 0:
            return 0
        clicked_count = EmailEvent.query.filter_by(user_id=self.id, clicked=True).count()
        return round((clicked_count / sent_count) * 100, 1)


class Campaign(db.Model):
    __tablename__ = 'campaign'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    template_name = db.Column(db.String(120), default="security_alert.html")
    frequency = db.Column(db.String(50), default="manual")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    email_events = db.relationship("EmailEvent", back_populates="campaign", lazy=True)


class EmailEvent(db.Model):
    __tablename__ = 'email_event'
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

    # Връзки
    user = db.relationship("User", back_populates="email_events")
    campaign = db.relationship("Campaign", back_populates="email_events")
    clicks = db.relationship("Click", back_populates="email_event", lazy=True)
    training_progress = db.relationship("TrainingProgress", back_populates="email_event", lazy=True)


class Click(db.Model):
    __tablename__ = 'click'
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    email_event_id = db.Column(db.Integer, db.ForeignKey("email_event.id"))

    ip = db.Column(db.String(100))
    user_agent = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Връзки
    user = db.relationship("User", back_populates="clicks")
    email_event = db.relationship("EmailEvent", back_populates="clicks")


class TrainingProgress(db.Model):
    __tablename__ = 'training_progress'
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    email_event_id = db.Column(db.Integer, db.ForeignKey("email_event.id"))

    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)

    # Връзки
    user = db.relationship("User", back_populates="training_progress")
    email_event = db.relationship("EmailEvent", back_populates="training_progress")
