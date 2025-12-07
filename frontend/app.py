# frontend/app.py
import streamlit as st
import requests, json, time, hashlib, os
from typing import Optional

# ---------- CONFIG ----------
API_BASE = "http://localhost:8000"   # backend address
USERS_FILE = os.path.join(os.path.dirname(__file__), "../data/users.json")
ADMIN_SECRET = "RANK"                # admin password (as requested)

# ---------- Helpers: users storage (simple hashed passwords) ----------
def _ensure_users_file():
    folder = os.path.dirname(USERS_FILE)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

def load_users():
    _ensure_users_file()
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    _ensure_users_file()
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def register_user(email: str, password: str) -> (bool, str):
    users = load_users()
    email = email.strip().lower()
    if email in users:
        return False, "Account already exists for this email."
    users[email] = {
        "password": hash_password(password),
        "created_at": int(time.time()),
        "is_admin": False
    }
    save_users(users)
    return True, "Registered successfully."

def authenticate_user(email: str, password: str) -> (bool, str, dict):
    users = load_users()
    email = email.strip().lower()
    if email not in users:
        return False, "No account with this email.", {}
    user = users[email]
    if user.get("password") != hash_password(password):
        return False, "Incorrect password.", {}
    return True, "Authenticated", {"email": email, "is_admin": user.get("is_admin", False)}

# ---------- Backend helpers ----------
def call_verify(provider: str, phone: str, address: str, timeout=15):
    payload = {"name": provider, "listed_phone": phone, "listed_address": address}
    r = requests.post(f"{API_BASE}/verify", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()

def save_search_history_local(username: str, provider: str, phone: str, address: str, result: dict):
    payload = {
        "username": username,
        "provider": provider,
        "listed_phone": phone,
        "listed_address": address,
        "timestamp": int(time.time()),
        "result": result
    }
    r = requests.post(f"{API_BASE}/history/record", json=payload, timeout=10)
    r.raise_for_status()
    return r.json()

def fetch_user_history(username: str):
    r = requests.get(f"{API_BASE}/history", params={"username": username})
    r.raise_for_status()
    return r.json()

def fetch_all_history():
    r = requests.get(f"{API_BASE}/history", params={"admin": True})
    r.raise_for_status()
    return r.json()

def submit_feedback(payload):
    r = requests.post(f"{API_BASE}/feedback", json=payload, timeout=12)
    r.raise_for_status()
    return r.json()

# ---------- Streamlit page styling (light health theme) ----------
st.set_page_config(page_title="HealthLens", layout="wide", page_icon="🩺")

_PAGE_CSS = """
<style>
body { background: #f6fbfb; }
.header { display:flex; align-items:center; gap:12px; }
.brand { font-size:28px; font-weight:700; color:#0b6e4f; }
.card { background: white; padding:18px; border-radius:10px; box-shadow: 0 6px 18px rgba(10,30,30,0.06); }
.navbar { background: linear-gradient(90deg,#e9f9f4,#ffffff); padding:12px; border-radius:8px; display:flex; gap:12px; align-items:center;}
.logo { font-weight:700; color:#0b6e4f; }
.btn { background-color:#0b6e4f; color:white; padding:6px 12px; border-radius:8px; }
.small { color:#6b6b6b; font-size:12px; }
.result-box { background:#fbffff; border-left:4px solid #0b6e4f; padding:12px; border-radius:8px;}
</style>
"""
st.markdown(_PAGE_CSS, unsafe_allow_html=True)

# ---------- Session: initialise ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"   # login / signup / verify / history / admin

# ---------- Top header / brand ----------
def render_header():
    col1, col2 = st.columns([3,1])
    with col1:
        st.markdown('<div class="header"><div class="logo">🩺 HealthLens</div><div style="margin-left:8px;"><span class="small">Provider Data Verification — Trusted, auditable, clinical-grade</span></div></div>', unsafe_allow_html=True)
    with col2:
        if st.session_state.logged_in:
            if st.button("Logout", key="top_logout"):
                st.session_state.logged_in = False
                st.session_state.user = None
                st.session_state.page = "login"
                st.success("Logged out")
                st.experimental_rerun()

render_header()
st.markdown("---")

# ---------- Login / Signup pages ----------
def show_login():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Welcome — Please sign in")
    role = st.radio("I am a", ("User","Admin"), index=0, horizontal=True)
    email = st.text_input("Email")
    pw = st.text_input("Password", type="password")
    col1, col2 = st.columns([1,1])
    login_clicked = False
    with col1:
        if st.button("Login"):
            login_clicked = True
    with col2:
        if st.button("Go to Sign up"):
            st.session_state.page = "signup"
            st.experimental_rerun()

    if login_clicked:
        if role == "Admin":
            # admin special: require secret admin password
            if pw == ADMIN_SECRET:
                st.session_state.logged_in = True
                st.session_state.user = {"email": email or "admin", "is_admin": True}
                st.session_state.page = "verify"
                st.success("Admin authenticated")
                st.experimental_rerun()
            else:
                st.error("Invalid admin password. Admin password is RANK.")
        else:
            # normal user auth
            ok, msg, user = authenticate_user(email, pw)
            if ok:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.session_state.page = "verify"
                st.success("Logged in")
                st.experimental_rerun()
            else:
                st.error(msg)
    st.markdown("</div>", unsafe_allow_html=True)

def show_signup():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Create a new account")
    email = st.text_input("Email", key="su_email")
    pw = st.text_input("Password", type="password", key="su_pw")
    pw2 = st.text_input("Confirm Password", type="password", key="su_pw2")
    if st.button("Sign up"):
        if not email or not pw:
            st.error("Enter email & password")
        elif pw != pw2:
            st.error("Passwords do not match")
        else:
            ok, msg = register_user(email, pw)
            if ok:
                st.success("Registered. You can now login.")
                st.session_state.page = "login"
                st.experimental_rerun()
            else:
                st.error(msg)
    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Navbar for logged in users ----------
def render_navbar():
    tabs = ["Verify", "History"]
    if st.session_state.user and st.session_state.user.get("is_admin"):
        tabs.append("Admin")
    cols = st.columns([1,1,6])
    with cols[0]:
        if st.button("🔎 Verify", key="nav_verify"):
            st.session_state.page = "verify"
            st.experimental_rerun()
    with cols[1]:
        if st.button("📚 History", key="nav_history"):
            st.session_state.page = "history"
            st.experimental_rerun()
    with cols[2]:
        # spacer / welcome
        if st.session_state.user:
            st.markdown(f"**Logged in as:** `{st.session_state.user.get('email')}`")
    st.markdown("---")

# ---------- Pages ----------
def page_verify():
    st.header("🔎 Find & Verify Provider")
    st.markdown("Enter provider details to validate across multiple public sources. Results are stored in your history.")
    with st.form("verify_form"):
        provider = st.text_input("Provider / Clinic Name", value="ABC Clinic")
        phone = st.text_input("Listed Phone", value="+91-9876543210")
        address = st.text_input("Listed Address", value="123 MG Road, City")
        submitted = st.form_submit_button("Verify Provider")
    if submitted:
        try:
            with st.spinner("Verifying provider..."):
                result = call_verify(provider.strip(), phone.strip(), address.strip())
            st.success("Verification complete")
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            col1, col2 = st.columns([1,2])
            with col1:
                st.metric("Confidence", result.get("final_confidence", result.get("confidence", 0)))
            with col2:
                st.write("Flag for review:", result.get("flag_for_manual_review", False))
                st.write("Sources: Local Scraper + OSM + registry")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("### 🏥 Best Matching Candidate")
            st.json(result.get("candidate"))

            st.markdown("### 📊 Field Scores")
            fs = result.get("field_scores", {})
            st.write("Name similarity:", fs.get("name"))
            st.write("Address similarity:", fs.get("address"))
            st.write("Phone match:", fs.get("phone"))

            # drift (if present)
            drift = result.get("drift")
            if drift and drift.get("drift_info"):
                st.markdown("### 🕘 Drift Detection")
                st.write("Drift score:", drift["drift_info"].get("drift_score"))
                st.write("Changed fields:", ", ".join(drift["drift_info"].get("changed_fields") or []) or "None")
                st.write("History count:", drift.get("history_count"))

            # save to history (backend)
            try:
                un = st.session_state.user.get("email") if st.session_state.user else "guest"
                save_search_history_local(un, provider.strip(), phone.strip(), address.strip(), result)
                st.success("Search saved to your history.")
            except Exception as e:
                st.error("Could not save to history: " + str(e))

        except Exception as e:
            st.error("Verification failed: " + str(e))

def page_history():
    st.header("📚 Your Search History")
    username = st.session_state.user.get("email") if st.session_state.user else None
    if st.session_state.user and st.session_state.user.get("is_admin"):
        st.info("Admin view — showing full search history.")
        try:
            all_hist = fetch_all_history()
            if not all_hist:
                st.info("No history records.")
                return
            for r in reversed(all_hist[-200:]):
                with st.expander(f"{r.get('provider')} — {time.ctime(r.get('timestamp'))}"):
                    st.write("User:", r.get("username"))
                    st.json(r.get("result"))
        except Exception as e:
            st.error("Failed to load history: " + str(e))
    else:
        if not username:
            st.info("No user logged in.")
            return
        try:
            my_hist = fetch_user_history(username)
            if not my_hist:
                st.info("No search history yet.")
                return
            for r in reversed(my_hist[-100:]):
                with st.expander(f"{r.get('provider')} — {time.ctime(r.get('timestamp'))}"):
                    st.write("Provider:", r.get("provider"))
                    st.write("Phone:", r.get("listed_phone"))
                    st.write("Address:", r.get("listed_address"))
                    st.write("Result summary:", r.get("result", {}).get("final_confidence") or r.get("result", {}).get("confidence"))
                    if st.button(f"Open result {r.get('timestamp')}", key=f"open{r.get('timestamp')}"):
                        st.json(r.get("result"))
        except Exception as e:
            st.error("Failed to load user history: " + str(e))

def page_admin():
    st.header("🛠 Admin Panel")
    st.markdown("Approve corrections or view / export history.")
    try:
        all_hist = fetch_all_history()
        st.write("Total searches:", len(all_hist))
    except Exception as e:
        st.error("Failed to load history: " + str(e))
        return

    st.markdown("### Quick Approve / Correct")
    with st.form("admin_approve"):
        provider = st.text_input("Provider name")
        corrected_name = st.text_input("Corrected name")
        corrected_address = st.text_input("Corrected address")
        corrected_phone = st.text_input("Corrected phone")
        accepted_source = st.text_input("Accepted candidate source (optional)")
        submitted_admin = st.form_submit_button("Submit correction")
    if submitted_admin:
        payload = {
            "provider_name": provider,
            "corrected_name": corrected_name,
            "corrected_address": corrected_address,
            "corrected_phone": corrected_phone,
            "accepted_candidate_source": accepted_source or None,
            "decision": "approve",
            "admin_user": st.session_state.user.get("email") or "admin"
        }
        try:
            resp = submit_feedback(payload)
            st.success("Correction submitted")
            st.json(resp)
        except Exception as e:
            st.error("Submit failed: " + str(e))

    st.markdown("### Export")
    if st.button("Download full history JSON"):
        try:
            data = fetch_all_history()
            st.download_button("Download JSON", data=json.dumps(data, indent=2), file_name="history_export.json")
        except Exception as e:
            st.error("Export failed: " + str(e))

# ---------- Routing logic ----------
if not st.session_state.logged_in:
    if st.session_state.page == "signup":
        show_signup()
    else:
        show_login()
else:
    # logged in -> show navbar and pages
    render_navbar()
    # route
    page = st.session_state.page or "verify"
    if page == "verify":
        page_verify()
    elif page == "history":
        page_history()
    elif page == "admin":
        if st.session_state.user and st.session_state.user.get("is_admin"):
            page_admin()
        else:
            st.error("Admin access required.")
    else:
        page_verify()
