import os
import uuid
from datetime import datetime, timedelta
from collections import Counter

from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from sqlalchemy import text

from config import Config
from models import db, User, Click, Campaign, EmailEvent, TrainingProgress
from email_service import send_training_email


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


with app.app_context():
    db.create_all()


def admin_required():
    return session.get("admin") is True


def get_client_ip():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    if ip and "," in ip:
        ip = ip.split(",")[0].strip()

    return ip


def get_default_campaign():
    campaign = Campaign.query.filter_by(name="Базово обучение").first()

    if not campaign:
        campaign = Campaign(
            name="Базово обучение",
            template_name="security_alert.html",
            frequency="manual"
        )
        db.session.add(campaign)
        db.session.commit()

    return campaign


def create_and_send_email(user, campaign):
    token = uuid.uuid4().hex

    event = EmailEvent(
        user_id=user.id,
        campaign_id=campaign.id,
        token=token,
        delivery_status="created"
    )

    db.session.add(event)
    db.session.commit()

    training_link = url_for("training_page", token=token, _external=True)
    open_pixel_url = url_for("open_pixel", token=token, _external=True)

    success = send_training_email(
        user=user,
        link=training_link,
        campaign=campaign,
        open_pixel_url=open_pixel_url
    )

    event.delivery_status = "sent" if success else "failed"
    db.session.commit()

    return success


# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect(url_for("login"))


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")

        if username == admin_username and password == admin_password:
            session["admin"] = True
            return redirect(url_for("dashboard"))

        flash("Невалидно потребителско име или парола.", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if not admin_required():
        return redirect(url_for("login"))

    users = User.query.all()
    users_count = len(users)
    clicks_count = Click.query.count()
    emails_count = EmailEvent.query.count()

    clicked_events = EmailEvent.query.filter_by(clicked=True).count()
    opened_events = EmailEvent.query.filter_by(opened=True).count()

    click_rate = round((clicked_events / emails_count) * 100, 1) if emails_count else 0
    open_rate = round((opened_events / emails_count) * 100, 1) if emails_count else 0

    high_risk_users = len([u for u in users if (u.risk_score or 0) > 5])

    today = datetime.utcnow().date()
    labels = []
    clicks_data = []

    all_clicks = Click.query.all()
    click_dates = Counter()

    for c in all_clicks:
        if c.timestamp:
            click_dates[c.timestamp.date()] += 1

    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime("%d.%m"))
        clicks_data.append(click_dates.get(day, 0))

    risk_labels = [u.email for u in users]
    risk_values = [u.risk_score or 0 for u in users]

    return render_template(
        "dashboard.html",
        users_count=users_count,
        clicks_count=clicks_count,
        emails_count=emails_count,
        click_rate=click_rate,
        open_rate=open_rate,
        high_risk_users=high_risk_users,
        chart_labels=labels,
        clicks_data=clicks_data,
        risk_labels=risk_labels,
        risk_values=risk_values
    )


# ---------------- USERS ----------------
@app.route("/users")
def users():
    if not admin_required():
        return redirect(url_for("login"))

    users_list = User.query.order_by(User.id.desc()).all()
    return render_template("users.html", users=users_list)


# ---------------- USER DETAIL ----------------
@app.route("/user/<int:user_id>")
def user_detail(user_id):
    if not admin_required():
        return redirect(url_for("login"))

    user = User.query.get_or_404(user_id)

    sent_count = EmailEvent.query.filter_by(user_id=user.id).count()
    clicked_count = EmailEvent.query.filter_by(user_id=user.id, clicked=True).count()
    opened_count = EmailEvent.query.filter_by(user_id=user.id, opened=True).count()
    completed_count = TrainingProgress.query.filter_by(user_id=user.id, completed=True).count()

    click_rate = round((clicked_count / sent_count) * 100, 1) if sent_count else 0
    open_rate = round((opened_count / sent_count) * 100, 1) if sent_count else 0

    today = datetime.utcnow().date()
    labels = []
    click_data = []

    click_dates = Counter()

    for c in user.clicks:
        if c.timestamp:
            click_dates[c.timestamp.date()] += 1

    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime("%d.%m"))
        click_data.append(click_dates.get(day, 0))

    return render_template(
        "user_detail.html",
        user=user,
        sent_count=sent_count,
        clicked_count=clicked_count,
        opened_count=opened_count,
        completed_count=completed_count,
        click_rate=click_rate,
        open_rate=open_rate,
        chart_labels=labels,
        click_data=click_data
    )


# ---------------- ADD USER ----------------
@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if not admin_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        email = request.form.get("email")

        if not email:
            flash("Имейлът е задължителен.", "error")
            return redirect(url_for("add_user"))

        existing = User.query.filter_by(email=email).first()

        if existing:
            flash("Този потребител вече съществува.", "warning")
            return redirect(url_for("users"))

        try:
            user = User(email=email, risk_score=0)
            db.session.add(user)
            db.session.commit()
            flash("Потребителят е добавен успешно.", "success")

        except Exception as e:
            db.session.rollback()
            print("DB ERROR:", e)
            flash("Грешка при запис в базата данни.", "error")

        return redirect(url_for("users"))

    return render_template("add_user.html")


# ---------------- SEND EMAIL TO ONE USER ----------------
@app.route("/send/<int:user_id>")
def send(user_id):
    if not admin_required():
        return redirect(url_for("login"))

    user = User.query.get(user_id)

    if not user:
        flash("Потребителят не е намерен.", "error")
        return redirect(url_for("users"))

    campaign = get_default_campaign()

    success = create_and_send_email(user, campaign)

    if success:
        flash("Имейлът е изпратен успешно.", "success")
    else:
        flash("Имейлът не беше изпратен.", "error")

    return redirect(url_for("users"))


# ---------------- CAMPAIGNS ----------------
@app.route("/campaigns")
def campaigns():
    if not admin_required():
        return redirect(url_for("login"))

    campaign_list = Campaign.query.order_by(Campaign.id.desc()).all()
    return render_template("campaigns.html", campaigns=campaign_list)


@app.route("/create_campaign", methods=["GET", "POST"])
def create_campaign():
    if not admin_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name")
        frequency = request.form.get("frequency")

        if not name:
            flash("Името на кампанията е задължително.", "error")
            return redirect(url_for("create_campaign"))

        campaign = Campaign(
            name=name,
            template_name="security_alert.html",
            frequency=frequency or "manual"
        )

        db.session.add(campaign)
        db.session.commit()

        flash("Кампанията е създадена успешно.", "success")
        return redirect(url_for("campaigns"))

    return render_template("create_campaign.html")


@app.route("/send_campaign/<int:campaign_id>")
def send_campaign(campaign_id):
    if not admin_required():
        return redirect(url_for("login"))

    campaign = Campaign.query.get_or_404(campaign_id)
    users = User.query.all()

    sent = 0
    failed = 0

    for user in users:
        success = create_and_send_email(user, campaign)
        if success:
            sent += 1
        else:
            failed += 1

    flash(f"Кампанията е изпратена. Успешни: {sent}, неуспешни: {failed}", "success")
    return redirect(url_for("campaigns"))


# ---------------- PUBLIC TRAINING PAGE ----------------
@app.route("/training/<token>")
def training_page(token):
    event = EmailEvent.query.filter_by(token=token).first_or_404()

    if not event.clicked:
        event.clicked = True
        event.clicked_at = datetime.utcnow()

        if event.user:
            event.user.risk_score = (event.user.risk_score or 0) + 1

    event.click_count = (event.click_count or 0) + 1

    click = Click(
        user_id=event.user_id,
        email_event_id=event.id,
        ip=get_client_ip(),
        user_agent=request.headers.get("User-Agent")
    )

    db.session.add(click)
    db.session.commit()

    return render_template("public_training.html", event=event, completed=False)


@app.route("/training/<token>/complete", methods=["POST"])
def complete_training(token):
    event = EmailEvent.query.filter_by(token=token).first_or_404()

    progress = TrainingProgress.query.filter_by(
        user_id=event.user_id,
        email_event_id=event.id
    ).first()

    if not progress:
        progress = TrainingProgress(
            user_id=event.user_id,
            email_event_id=event.id
        )
        db.session.add(progress)

    progress.completed = True
    progress.completed_at = datetime.utcnow()

    db.session.commit()

    return render_template("public_training.html", event=event, completed=True)


# ---------------- OPEN PIXEL ----------------
@app.route("/open/<token>.png")
def open_pixel(token):
    event = EmailEvent.query.filter_by(token=token).first()

    if event:
        if not event.opened:
            event.opened = True
            event.opened_at = datetime.utcnow()

        event.open_count = (event.open_count or 0) + 1
        db.session.commit()

    pixel = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00"
        b"\x00\x00\x00\x00\x00\x00!\xf9\x04\x01"
        b"\x00\x00\x00\x00,\x00\x00\x00\x00\x01"
        b"\x00\x01\x00\x00\x02\x02D\x01\x00;"
    )

    return Response(pixel, mimetype="image/gif")


# ---------------- CLICKS ----------------
@app.route("/clicks")
def clicks():
    if not admin_required():
        return redirect(url_for("login"))

    click_list = Click.query.order_by(Click.timestamp.desc()).all()
    return render_template("clicks.html", clicks=click_list)


# ---------------- STATISTICS ----------------
@app.route("/statistics")
def statistics():
    if not admin_required():
        return redirect(url_for("login"))

    users = User.query.all()

    labels = [u.email for u in users]
    risk_scores = [u.risk_score or 0 for u in users]
    click_rates = [u.click_rate() for u in users]

    return render_template(
        "statistics.html",
        labels=labels,
        risk_scores=risk_scores,
        click_rates=click_rates
    )


# ---------------- FIX DATABASE ----------------
@app.route("/fix-db")
def fix_db():
    if not admin_required():
        return redirect(url_for("login"))

    with app.app_context():
        db.create_all()

    commands = [
        "ALTER TABLE click ADD COLUMN ip VARCHAR(100);",
        "ALTER TABLE click ADD COLUMN timestamp TIMESTAMP;",
        "ALTER TABLE click ADD COLUMN email_event_id INTEGER;",
        "ALTER TABLE click ADD COLUMN user_agent VARCHAR(300);"
    ]

    for command in commands:
        try:
            db.session.execute(text(command))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("MIGRATION:", e)

    return "Базата е обновена успешно."


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
