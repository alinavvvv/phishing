import os
from flask import Flask, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# =====================
# SAFE SECRET KEY
# =====================
app.secret_key = os.environ.get("SECRET_KEY", "dev-key")

# =====================
# SAFE DATABASE HANDLING (IMPORTANT FIX)
# =====================
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    # fallback so Render NEVER crashes
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

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
# SAFE DB INIT (NO CRASH)
# =====================
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print("DB INIT ERROR:", e)

# =====================
# ROUTES
# =====================
@app.route("/")
def home():
    return "<h1>SOC System OK</h1>"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["admin"] = True
        return redirect("/dashboard")

    return "<form method='post'><button>Login</button></form>"

@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")

    return "<h1>Dashboard OK</h1>"

@app.route("/users")
def users():
    if not session.get("admin"):
        return redirect("/login")

    users = User.query.all()
    return "<br>".join([u.email for u in users])

@app.route("/add_user", methods=["POST", "GET"])
def add_user():
    if request.method == "POST":
        email = request.form["email"]

        if email:
            exists = User.query.filter_by(email=email).first()
            if not exists:
                db.session.add(User(email=email))
                db.session.commit()

        return redirect("/users")

    return """
    <form method="post">
        <input name="email">
        <button>Add</button>
    </form>
    """

@app.route("/track")
def track():
    user_id = request.args.get("id")

    try:
        user_id = int(user_id)
    except:
        return "invalid"

    db.session.add(Click(user_id=user_id, ip=request.remote_addr))
    db.session.commit()

    return "tracked"

# =====================
# IMPORTANT FOR RENDER
# =====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
