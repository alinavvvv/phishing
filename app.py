from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import Config
from models import db, User, Click
from flask_mail import Mail
from email_service import send_phishing_email

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
mail = Mail(app)

# ---------------- INIT DB ----------------
with app.app_context():
    db.create_all()

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

        try:
            user = User(email=email, risk_score=0)  # ✅ добавих default
            db.session.add(user)
            db.session.commit()
            flash("User added successfully", "success")

        except Exception:
            db.session.rollback()
            flash("Database error", "error")

        return redirect(url_for("users"))

    return render_template("add_user.html")


# ---------------- SEND EMAIL ----------------
@app.route("/send/<int:user_id>")
def send(user_id):
    user = User.query.get(user_id)

    if not user:
        flash("User not found", "error")
        return redirect(url_for("users"))

    link = request.host_url + f"track?id={user.id}"

    try:
        send_phishing_email(user, link)
        flash("Email sent!", "success")
        print("SEND BUTTON CLICKED")

    except Exception as e:
        print("SEND ERROR:", e)
        flash("Email failed", "error")

    return redirect(url_for("users"))

# ---------------- TRACK CLICK ----------------
@app.route("/track")
def track():
    user_id = request.args.get("id")

    try:
        user_id = int(user_id)
    except:
        return redirect(url_for("education"))

    user = User.query.get(user_id)

    if user:
        user.risk_score = (user.risk_score or 0) + 1

        click = Click(
            user_id=user.id,
            ip=request.headers.get("X-Forwarded-For", request.remote_addr)
        )

        db.session.add(click)
        db.session.commit()

    return redirect(url_for("education"))


@app.route("/clicks")
def clicks():
    if not session.get("admin"):
        return redirect(url_for("login"))

    click_list = Click.query.order_by(Click.timestamp.desc()).all()
    return render_template("clicks.html", clicks=click_list)

# ---------------- EDUCATION PAGE ----------------
@app.route("/education")
def education():
    return render_template("education.html")


# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
