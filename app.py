import os
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

app = Flask(__name__)

# SECRET KEY
app.secret_key = os.environ.get("SECRET_KEY", "dev-key")

# DATABASE (safe fallback)
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL or "sqlite:///local.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# MAIL (optional)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")

mail = Mail(app)

# MODELS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)

class Click(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)

with app.app_context():
    db.create_all()

# HOME
@app.route("/")
def home():
    return redirect("/login")

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["admin"] = True
        return redirect("/dashboard")
    return render_template("login.html")

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")
    return render_template("dashboard.html")

# USERS
@app.route("/users")
def users():
    if not session.get("admin"):
        return redirect("/login")

    users = User.query.all()
    return render_template("users.html", users=users)

# ADD USER
@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        email = request.form["email"]
        if email:
            db.session.add(User(email=email))
            db.session.commit()
        return redirect("/users")

    return render_template("add_user.html")

# EDUCATION
@app.route("/education")
def education():
    return render_template("education.html")

# RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
