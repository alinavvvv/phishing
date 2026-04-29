from flask import Flask, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
import os

app = Flask(__name__)

# =====================
# CONFIG
# =====================
app.secret_key = os.environ.get("SECRET_KEY", "change-me")

# 🔥 POSTGRES ONLY (Render requirement)
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL or "sqlite:///local.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =====================
# MAIL (SAFE)
# =====================
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_USERNAME")

mail = Mail(app)

# =====================
# MODELS
# =====================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    risk_score = db.Column(db.Integer, default=0)

class Click(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    ip = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# =====================
# SAFE INIT (ONLY ON START)
# =====================
with app.app_context():
    db.create_all()

# =====================
# HOME
# =====================
@app.route("/")
def home():
    return "<h1>🛡 SOC Training Platform</h1><a href='/login'>Login</a>"

# =====================
# LOGIN
# =====================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["admin"] = True
        return redirect("/dashboard")

    return """
    <form method="post">
        <input name="username">
        <input name="password" type="password">
        <button>Login</button>
    </form>
    """

# =====================
# USERS
# =====================
@app.route("/users")
def users():
    if not session.get("admin"):
        return redirect("/login")

    users = User.query.all()

    rows = ""
    for u in users:
        level = "LOW"
        if u.risk_score > 5:
            level = "HIGH"
        elif u.risk_score > 2:
            level = "MEDIUM"

        rows += f"""
        <tr>
            <td>{u.id}</td>
            <td>{u.email}</td>
            <td>{u.risk_score}</td>
            <td>{level}</td>
            <td><a href="/send_email/{u.id}">send</a></td>
        </tr>
        """

    return f"""
    <h1>Users</h1>
    <table border="1">
        <tr><th>ID</th><th>Email</th><th>Risk</th><th>Level</th><th>Action</th></tr>
        {rows}
    </table>
    """

# =====================
# ADD USER
# =====================
@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        email = request.form["email"]

        if not User.query.filter_by(email=email).first():
            db.session.add(User(email=email))
            db.session.commit()

        return redirect("/users")

    return """
    <form method="post">
        <input name="email">
        <button>Add</button>
    </form>
    """

# =====================
# EMAIL (NON-BLOCKING SAFE)
# =====================
@app.route("/send_email/<int:user_id>")
def send_email(user_id):
    if not session.get("admin"):
        return redirect("/login")

    user = User.query.get(user_id)
    if not user:
        return "not found"

    link = f"{request.host_url}track?id={user_id}"

    try:
        msg = Message(
            subject="Security Training",
            recipients=[user.email],
            html=f"<p>Training simulation</p><a href='{link}'>Open</a>"
        )

        mail.send(msg)

    except Exception as e:
        print("MAIL ERROR:", e)

    return redirect("/users")

# =====================
# TRACK
# =====================
@app.route("/track")
def track():
    user_id = int(request.args.get("id"))

    db.session.add(Click(user_id=user_id, ip=request.remote_addr))

    user = User.query.get(user_id)
    if user:
        user.risk_score += 1

    db.session.commit()

    return "<h1>Training page</h1>"

# =====================
# DASHBOARD
# =====================
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")

    clicks = Click.query.count()

    return f"<h1>Dashboard</h1><p>Total clicks: {clicks}</p>"

# =====================
# RUN
# =====================
   if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
