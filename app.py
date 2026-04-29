from flask import Flask, render_template, request, redirect, session
from config import Config
from models import db, User, Click
from flask_mail import Mail
from email_service import send_phishing_email

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
mail = Mail(app)

with app.app_context():
    db.create_all()

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["admin"] = True
        return redirect("/dashboard")
    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")

    users = User.query.count()
    clicks = Click.query.count()

    return render_template("dashboard.html", users=users, clicks=clicks)

# ---------------- USERS ----------------
@app.route("/users")
def users():
    if not session.get("admin"):
        return redirect("/login")

    users = User.query.all()
    return render_template("users.html", users=users)

# ---------------- ADD USER ----------------
@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        email = request.form["email"]

        if not User.query.filter_by(email=email).first():
            db.session.add(User(email=email))
            db.session.commit()

        return redirect("/users")

    return render_template("add_user.html")

# ---------------- SEND EMAIL ----------------
@app.route("/send/<int:user_id>")
def send(user_id):
    user = User.query.get(user_id)

    link = request.host_url + f"track?id={user.id}"

    send_phishing_email(mail, user, link)

    return redirect("/users")

# ---------------- TRACK ----------------
@app.route("/track")
def track():
    user_id = request.args.get("id")

    user = User.query.get(user_id)
    if user:
        user.risk_score += 2

    db.session.add(Click(user_id=user_id, ip=request.remote_addr))
    db.session.commit()

    return redirect("/education")

# ---------------- EDUCATION ----------------
@app.route("/education")
def education():
    return render_template("education.html")
