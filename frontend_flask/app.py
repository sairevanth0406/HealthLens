from flask import Flask, render_template, request, redirect, session, jsonify
import requests, json, time, hashlib, os

API_BASE = "http://localhost:8000"
ADMIN_PASSWORD = "RANK"

app = Flask(__name__)
from datetime import datetime
@app.template_filter('datetimeformat')
def datetimeformat(value):
    try:
        ts = int(value)
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return str(value)

app.secret_key = "healthlens_secret_key"

USERS_FILE = "users.json"

# ----------------------------
# Helpers
# ----------------------------
def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


# ----------------------------
# ROUTES
# ----------------------------

@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")


# LOGIN -----------------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        email = request.form.get("email")
        password = request.form.get("password")

        # Admin login
        if role == "admin":
            if password == ADMIN_PASSWORD:
                session["user"] = {"email": "admin", "admin": True}
                return redirect("/dashboard")
            else:
                return render_template("login.html", error="Invalid Admin Password")

        # User login
        users = load_users()
        if email in users and users[email]["password"] == hash_pw(password):
            session["user"] = {"email": email, "admin": False}
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# SIGNUP -----------------------
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        pw = request.form.get("password")
        pw2 = request.form.get("password2")

        if pw != pw2:
            return render_template("signup.html", error="Passwords do not match")

        users = load_users()

        if email in users:
            return render_template("signup.html", error="User already exists")

        users[email] = {"password": hash_pw(pw), "created": time.time()}
        save_users(users)

        return redirect("/login")

    return render_template("signup.html")


# DASHBOARD -----------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html", user=session["user"])


# VERIFY PROVIDER ------------------
@app.route("/verify", methods=["GET","POST"])
def verify():
    if "user" not in session:
        return redirect("/login")

    result = None
    if request.method == "POST":
        provider = request.form.get("provider")
        phone = request.form.get("phone")
        address = request.form.get("address")

        payload = {
            "name": provider,
            "listed_phone": phone,
            "listed_address": address
        }
        r = requests.post(f"{API_BASE}/verify", json=payload)
        result = r.json()

        # save history
        history_payload = {
            "username": session["user"]["email"],
            "provider": provider,
            "listed_phone": phone,
            "listed_address": address,
            "result": result,
            "timestamp": int(time.time())
        }
        requests.post(f"{API_BASE}/history/record", json=history_payload)

    return render_template("verify.html", result=result, user=session["user"])


# USER HISTORY ----------------------
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    email = session["user"]["email"]
    if session["user"]["admin"]:
        r = requests.get(f"{API_BASE}/history", params={"admin": True})
    else:
        r = requests.get(f"{API_BASE}/history", params={"username": email})

    data = r.json()
    return render_template("history.html", history=data, user=session["user"])


# ADMIN PANEL ------------------------
@app.route("/admin", methods=["GET","POST"])
def admin_page():
    if "user" not in session or not session["user"]["admin"]:
        return redirect("/login")

    response = None
    if request.method == "POST":
        payload = {
            "provider_name": request.form.get("provider"),
            "corrected_name": request.form.get("name"),
            "corrected_address": request.form.get("address"),
            "corrected_phone": request.form.get("phone"),
            "accepted_candidate_source": request.form.get("source"),
            "decision": "approve",
            "admin_user": "admin"
        }
        r = requests.post(f"{API_BASE}/feedback", json=payload)
        response = r.json()

    return render_template("admin.html", response=response, user=session["user"])


# LOGOUT -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# RUN APP ----------------------------
if __name__ == "__main__":
    app.run(debug=True, port=10000)
