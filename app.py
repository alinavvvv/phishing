import os
from flask import Flask, request, redirect, session, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# =====================
# CONFIG (IMPORTANT FOR RENDER)
# =====================
app.secret_key = os.environ.get("SECRET_KEY", "dev-key")

# Fix DATABASE_URL safely
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Render sometimes gives postgres:// instead of postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    # fallback so app NEVER crashes
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

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
# INIT DB
# =====================
with app.app_context():
    db.create_all()

# =====================
# HOME
# =====================
@app.route("/")
def home():
    return "<h1>SOC Training System</h1><a href='/login'>Login</a>"

# =====================
# LOGIN (dummy)
# =====================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["admin"] = True
        return redirect("/dashboard")

    return """
    <form method="post">
        <input name="username" placeholder="admin"><br>
        <input name="password" type="password"><br>
        <button>Login</button>
    </form>
    """

# =====================
# DASHBOARD
# =====================
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")

    clicks = Click.query.count()

    return f"""
    <h1>Dashboard</h1>
    <p>Total clicks: {clicks}</p>
    <a href="/users">Users</a>
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
        rows += f"<tr><td>{u.id}</td><td>{u.email}</td><td>{u.risk_score}</td></tr>"

    return f"""
    <h1>Users</h1>
    <a href="/add_user">Add user</a>
    <table border="1">
        <tr><th>ID</th><th>Email</th><th>Risk</th></tr>
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

        if email and not User.query.filter_by(email=email).first():
            db.session.add(User(email=email))
            db.session.commit()

        return redirect("/users")

    return """
    <form method="post">
        <input name="email" placeholder="email">
        <button>Add</button>
    </form>
    """

# =====================
# TRACK (SAFE)
# =====================
@app.route("/track")
def track():
    user_id = request.args.get("id")

    try:
        user_id = int(user_id)
    except:
        return "invalid"

    db.session.add(Click(user_id=user_id, ip=request.remote_addr))

    user = User.query.get(user_id)
    if user:
        user.risk_score += 1

    db.session.commit()

    return "<h1>OK tracked</h1>"

# =====================
# RUN (RENDER SAFE)
# =====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
