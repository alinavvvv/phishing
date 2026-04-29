from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import Config
from models import db, User, Click
from flask_mail import Mail
from email_service import send_training_email

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
mail = Mail(app)

# ---------------- INIT DB ----------------
with app.app_context():
    db.create_all()


# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect(url_for("login"))


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["admin"] = True
        return redirect(url_for("dashboard"))

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("login"))

    users_count = User.query.count()
    clicks_count = Click.query.count()

    return render_template(
        "dashboard.html",
        users=users_count,
        clicks=clicks_count
    )


# ---------------- USERS ----------------
@app.route("/users")
def users():
    if not session.get("admin"):
        return redirect(url_for("login"))

    users_list = User.query.all()
    return render_template("users.html", users=users_list)


# ---------------- ADD USER ----------------
@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if not session.get("admin"):
        return redirect(url_for("login"))

    if request.method == "POST":
        email = request.form.get("email")

        if not email:
            flash("Email is required", "error")
            return redirect(url_for("add_user"))

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("User already exists", "warning")
            return redirect(url_for("users"))

        user = User(email=email)
        db.session.add(user)
        db.session.commit()

        flash("User added successfully", "success")
        return redirect(url_for("users"))

    return render_template("add_user.html")


# ---------------- TRAINING EMAIL (SAFE) ----------------
@app.route("/send/<int:user_id>")
def send(user_id):
    if not session.get("admin"):
        return redirect(url_for("login"))

    user = User.query.get(user_id)

    if not user:
        flash("User not found", "error")
        return redirect(url_for("users"))

    try:
        send_training_email(mail, user)
        flash(f"Email sent to {user.email}", "success")
    except Exception as e:
        flash("Email failed to send", "error")
        print(e)

    return redirect(url_for("users"))


# ---------------- TRACK CLICK (SIMULATION ONLY) ----------------
@app.route("/track")
def track():
    user_id = request.args.get("id")

    user = User.query.get(user_id)

    if user:
        user.risk_score = (user.risk_score or 0) + 1

    if user_id:
        db.session.add(Click(user_id=user_id))

    db.session.commit()

    return redirect(url_for("education"))


# ---------------- EDUCATION ----------------
@app.route("/education")
def education():
    return render_template("education.html")


if __name__ == "__main__":
    app.run(debug=True)
