from flask import Flask, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "soc-final")

# =====================
# DATABASE
# =====================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///phishing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =====================
# EMAIL
# =====================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get("MAIL_USERNAME")

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
# SAFE DB INIT (IMPORTANT FIX)
# =====================
@app.before_request
def init_db():
    db.create_all()

# =====================
# HOME
# =====================
@app.route("/")
def home():
    return "<h1>🛡 SOC Training System</h1><a href='/login'>Admin Login</a>"

# =====================
# LOGIN
# =====================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["admin"] = True
        return redirect("/dashboard")

    return """
    <h2>Admin Login</h2>
    <form method="post">
        <input name="username"><br><br>
        <input name="password" type="password"><br><br>
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

    all_users = User.query.all()

    rows = ""
    for u in all_users:
        level = "🟢 LOW"
        if u.risk_score > 5:
            level = "🔴 HIGH"
        elif u.risk_score > 2:
            level = "🟡 MEDIUM"

        rows += f"""
        <tr>
            <td>{u.id}</td>
            <td>{u.email}</td>
            <td>{u.risk_score}</td>
            <td>{level}</td>
            <td>
                <a href="/send_email/{u.id}?lang=bg">BG</a> |
                <a href="/send_email/{u.id}?lang=en">EN</a>
            </td>
        </tr>
        """

    return f"""
    <h1>👥 Users</h1>
    <a href="/add_user">Add User</a><br><br>
    <table border="1" cellpadding="10">
        <tr><th>ID</th><th>Email</th><th>Risk</th><th>Level</th><th>Send</th></tr>
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
    <h2>Add User</h2>
    <form method="post">
        <input name="email">
        <button>Add</button>
    </form>
    """

# =====================
# SEND EMAIL
# =====================
@app.route("/send_email/<int:user_id>")
def send_email(user_id):
    if not session.get("admin"):
        return redirect("/login")

    user = User.query.get(user_id)
    if not user:
        return "User not found"

    lang = request.args.get("lang", "en")

    link = f"{request.host_url}track?id={user_id}&lang={lang}"

    msg = Message(
        subject="Security Training",
        recipients=[user.email],
        html=f"<p>Training email</p><a href='{link}'>Open</a>"
    )

    try:
        mail.send(msg)
    except Exception as e:
        return f"Email error: {e}"

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
        return "Invalid"

    db.session.add(Click(user_id=user_id, ip=request.remote_addr))

    user = User.query.get(user_id)
    if user:
        user.risk_score += 1

    db.session.commit()

    return redirect("/education")

# =====================
# EDUCATION
# =====================
@app.route("/education")
def education():
    return "<h1>Security Training</h1><p>Awareness simulation.</p>"

# =====================
# DASHBOARD
# =====================
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")

    clicks = Click.query.count()

    return f"""
    <h1>📊 Dashboard</h1>
    <p>Total clicks: {clicks}</p>
    <a href="/users">Users</a>
    """

# =====================
# RUN
# =====================
if __name__ == "__main__":
    app.run()
