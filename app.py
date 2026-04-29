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
# EMAIL (GMAIL SMTP)
# =====================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config['MAIL_USE_TLS'] = True

mail = Mail(app)

# =====================
# MODELS
# =====================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    risk_score = db.Column(db.Integer, default=0)

class Click(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    ip = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

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

    users = User.query.all()

    rows = ""
    for u in users:
        if u.risk_score > 5:
            level = "🔴 HIGH"
        elif u.risk_score > 2:
            level = "🟡 MEDIUM"
        else:
            level = "🟢 LOW"

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
        <tr>
            <th>ID</th>
            <th>Email</th>
            <th>Risk</th>
            <th>Level</th>
            <th>Send</th>
        </tr>
        {rows}
    </table>
    """

# =====================
# ADD USER
# =====================
@app.route("/add_user", methods=["GET","POST"])
def add_user():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        email = request.form["email"]
        db.session.add(User(email=email))
        db.session.commit()
        return redirect("/users")

    return """
    <h2>Add User</h2>
    <form method="post">
        <input name="email" placeholder="email"><br><br>
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

    base_url = request.host_url
    link = f"{base_url}track?id={user_id}&lang={lang}"

    if lang == "bg":
        subject = "⚠️ Сигурност на акаунта"
        body = f"""
        <div style="font-family:Arial">
            <h2>Сигнал за сигурност</h2>
            <p>Засечена е необичайна активност.</p>
            <a href="{link}" style="background:#2563eb;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;">
                Потвърди акаунт
            </a>
        </div>
        """
    else:
        subject = "⚠️ Security Alert"
        body = f"""
        <div style="font-family:Arial">
            <h2>Security Alert</h2>
            <p>We detected unusual activity.</p>
            <a href="{link}" style="background:#2563eb;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;">
                Verify Account
            </a>
        </div>
        """

    msg = Message(subject=subject, recipients=[user.email], html=body)
    mail.send(msg)

    return redirect("/users")

# =====================
# TRACK
# =====================
@app.route("/track")
def track():
    user_id = request.args.get("id")
    lang = request.args.get("lang", "en")

    if not user_id:
        return "Invalid"

    user_id = int(user_id)

    db.session.add(Click(user_id=user_id, ip=request.remote_addr))

    user = User.query.get(user_id)
    if user:
        user.risk_score += 1

    db.session.commit()

    return redirect(f"/education?lang={lang}")

# =====================
# EDUCATION
# =====================
@app.route("/education")
def education():
    lang = request.args.get("lang", "en")

    bg = """
    <div style="display:flex;justify-content:center;align-items:center;height:100vh;background:#f3f4f6;font-family:Arial;">
        <div style="background:white;padding:40px;border-radius:12px;width:700px;box-shadow:0 10px 30px rgba(0,0,0,0.1);">

            <h1 style="color:red;">⚠ Фишинг симулация</h1>

            <p>Този имейл беше част от обучение по киберсигурност.</p>

            <h3>Какво беше подозрително?</h3>
            <ul>
                <li>Спешен тон</li>
                <li>Линк към външен сайт</li>
                <li>Искане за действие</li>
            </ul>

            <h3>Как да се предпазите:</h3>
            <ul>
                <li>Проверявайте подателя</li>
                <li>Не кликайте линкове</li>
                <li>Не въвеждайте пароли</li>
            </ul>

        </div>
    </div>
    """

    en = """
    <div style="display:flex;justify-content:center;align-items:center;height:100vh;background:#f3f4f6;font-family:Arial;">
        <div style="background:white;padding:40px;border-radius:12px;width:700px;box-shadow:0 10px 30px rgba(0,0,0,0.1);">

            <h1 style="color:red;">⚠ Phishing Simulation</h1>

            <p>This email was part of a cybersecurity training.</p>

            <h3>Warning signs:</h3>
            <ul>
                <li>Urgent tone</li>
                <li>External link</li>
                <li>Request for action</li>
            </ul>

            <h3>How to stay safe:</h3>
            <ul>
                <li>Verify sender</li>
                <li>Avoid suspicious links</li>
                <li>Never enter passwords</li>
            </ul>

        </div>
    </div>
    """

    return bg if lang == "bg" else en

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
    with app.app_context():
        db.create_all()

    app.run()
