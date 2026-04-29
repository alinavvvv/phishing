import os
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

# =====================
# APP INIT
# =====================
app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "dev-key")

# =====================
# DATABASE (Render-safe)
# =====================
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///local.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =====================
# MAIL (safe init)
# =====================
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")

mail = Mail(app)

# =====================
# MODELS (must exist in models.py)
# =====================
from models import User, Click

with app.app_context():
    db.create_all()

# =====================
# HOME (FIX FOR 404)
# =====================
@app.route("/")
def home():
    return redirect("/login")

# =====================
# LOGIN
# =====================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["admin"] = True
        return redirect("/dashboard")

    return render_template("login.html")

# =====================
# DASHBOARD
# =====================
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")

    users = User.query.count()
    clicks = Click.query.count()

    return render_template("dashboard.html", users=users, clicks=clicks)

# =====================
# USERS
# =====================
@app.route("/users")
def users():
    if not session.get("admin"):
        return redirect("/login")

    users = User.query.all()
    return render_template("users.html", users=users)

# =====================
# ADD USER
# =====================
@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        email = request.form.get("email")

        if email and not User.query.filter_by(email=email).first():
            db.session.add(User(email=email))
            db.session.commit()

        return redirect("/users")

    return render_template("add_user.html")

# =====================
# SEND EMAIL (simulation)
# =====================
@app.route("/send/<int:user_id>")
def send(user_id):
    if not session.get("admin"):
        return redirect("/login")

    user = User.query.get(user_id)
    if not user:
        return "User not found"

    link = request.host_url + f"track?id={user.id}"

    try:
        from email_service import send_phishing_email
        send_phishing_email(mail, user, link)
    except Exception as e:
        return f"Email error: {str(e)}"

    return redirect("/users")

# =====================
# TRACK
# =====================
@app.route("/track")
def track():
    user_id = request.args.get("id")

    try:
        user_id = int(user_id)
    except:
        return "Invalid link"

    user = User.query.get(user_id)

    if user:
        user.risk_score += 1

    db.session.add(Click(user_id=user_id, ip=request.remote_addr))
    db.session.commit()

    return redirect("/education")

# =====================
# EDUCATION
# =====================
@app.route("/education")
def education():
    return render_template("education.html")

# =====================
# RUN LOCAL ONLY
# =====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
