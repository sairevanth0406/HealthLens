# api/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, json, time

# Multi-Agent Controller
from agents.controller_agent import ControllerAgent

# Drift history loader
from verification.drift import load_history, record_snapshot

# Scraper imports for feedback logic
from scraper.phone_sources import match_hospital_key
from scraper.phone_scraper import scrape_phone_from_website

# Source credibility weight file
SOURCE_WEIGHTS_FILE = os.path.join(os.path.dirname(__file__), "../data/source_weights.json")

def load_source_weights():
    if not os.path.exists(SOURCE_WEIGHTS_FILE):
        return {}
    with open(SOURCE_WEIGHTS_FILE, "r") as f:
        return json.load(f)

def save_source_weights(w):
    with open(SOURCE_WEIGHTS_FILE, "w") as f:
        json.dump(w, f, indent=2)


# -----------------------------------------------------------
# FASTAPI APP
# -----------------------------------------------------------
app = FastAPI()
controller = ControllerAgent()


# -----------------------------------------------------------
# MODELS
# -----------------------------------------------------------
class ProviderIn(BaseModel):
    name: str
    listed_phone: str = None
    listed_address: str = None


class FeedbackIn(BaseModel):
    provider_name: str
    corrected_name: str = None
    corrected_address: str = None
    corrected_phone: str = None
    accepted_candidate_source: str = None
    decision: str        # "approve" or "reject"
    admin_user: str = "admin"


# -----------------------------------------------------------
# VERIFY ENDPOINT (MULTI-AGENT)
# -----------------------------------------------------------
@app.post("/verify")
async def verify(p: ProviderIn):
    """
    Main entry for provider verification.
    Goes through ScraperAgent → VerificationAgent → DriftAgent.
    """
    return controller.run(p.dict())


# -----------------------------------------------------------
# FEEDBACK (ADMIN CORRECTION)
# -----------------------------------------------------------
@app.post("/feedback")
async def feedback(f: FeedbackIn):
    """
    Admin approves or rejects a candidate.
    Updates source-credibility and stores correction snapshot.
    """

    if f.decision not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="decision must be approve/reject")

    weights = load_source_weights()
    lr = 0.05  # learning rate

    if f.accepted_candidate_source:
        src = f.accepted_candidate_source

        # APPROVE → increase credibility
        if f.decision == "approve":
            weights[src] = weights.get(src, 0.5) * (1 + lr)

        # REJECT → decrease credibility
        else:
            weights[src] = weights.get(src, 0.5) * (1 - lr)

        # Clamp values
        weights[src] = max(0.05, min(0.99, weights[src]))
        save_source_weights(weights)

    # Store correction snapshot
    snapshot = {
        "name": f.corrected_name or f.provider_name,
        "address": f.corrected_address,
        "phone": f.corrected_phone,
        "website": None,
        "retrieved_at": int(time.time())
    }

    try:
        rec = record_snapshot(f.provider_name, snapshot)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"snapshot error: {e}")

    return {
        "status": "ok",
        "weights_updated": True,
        "new_snapshot": rec
    }


# -----------------------------------------------------------
# ADMIN HISTORY (ONE NAME ONLY!)
# -----------------------------------------------------------
@app.get("/admin/history")
async def get_admin_history():
    """Return full drift history for admin."""
    return load_history()


# -----------------------------------------------------------
# USER SEARCH HISTORY
# -----------------------------------------------------------
SEARCH_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "../data/search_history.json")

def _ensure_search_history_file():
    folder = os.path.dirname(SEARCH_HISTORY_FILE)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    if not os.path.exists(SEARCH_HISTORY_FILE):
        with open(SEARCH_HISTORY_FILE, "w") as f:
            json.dump([], f)

def load_search_history():
    _ensure_search_history_file()
    with open(SEARCH_HISTORY_FILE, "r") as f:
        return json.load(f)

def save_search_history(arr):
    _ensure_search_history_file()
    with open(SEARCH_HISTORY_FILE, "w") as f:
        json.dump(arr, f, indent=2, ensure_ascii=False)


@app.post("/history/record")
async def record_user_search(payload: dict):
    """
    Record a user's search query and verification summary.
    """
    try:
        data = load_search_history()
        payload.setdefault("timestamp", int(time.time()))
        data.append(payload)
        save_search_history(data)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def get_user_history(username: str = None, admin: bool = False):
    """
    - If admin=True → return all searches  
    - If username provided → return that user's searches  
    """
    data = load_search_history()

    if admin:
        return data

    if username:
        return [x for x in data if x.get("username") == username]

    return []
