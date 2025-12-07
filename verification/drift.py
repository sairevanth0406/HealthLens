# verification/drift.py
import os
import json
import time
from pathlib import Path
from rapidfuzz import fuzz

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "../data/history.json")

def _ensure_history_file():
    p = Path(HISTORY_PATH)
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text(json.dumps({}), encoding="utf-8")

def _slug(name):
    if not name:
        return "unknown"
    s = "".join(ch.lower() if ch.isalnum() else "-" for ch in name)
    s = "-".join([part for part in s.split("-") if part])
    return s[:200]

def load_history():
    _ensure_history_file()
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_history(hist):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2, ensure_ascii=False)

def _text_sim(a, b):
    if not a or not b:
        return 0.0
    try:
        return fuzz.token_sort_ratio(str(a), str(b)) / 100.0
    except:
        return 0.0

def _phone_sim(a, b):
    if not a or not b:
        return 0.0
    na = "".join(filter(str.isdigit, str(a)))
    nb = "".join(filter(str.isdigit, str(b)))
    return 1.0 if na and nb and na == nb else 0.0

def compute_drift_score(old, new):
    """
    old/new are dicts with keys name, address, phone (candidate snapshot).
    returns drift_info: { field_diffs: {...}, drift_score (0..100), changed_fields: [..] }
    Higher drift_score => more change (0 = identical)
    """
    # field similarity (1.0 = identical)
    s_name = _text_sim(old.get("name"), new.get("name"))
    s_addr = _text_sim(old.get("address"), new.get("address"))
    s_phone = _phone_sim(old.get("phone"), new.get("phone"))

    # per-field drift = (1 - similarity)
    d_name = 1.0 - s_name
    d_addr = 1.0 - s_addr
    d_phone = 1.0 - s_phone

    # weights (you can tune)
    w_name, w_addr, w_phone = 0.4, 0.35, 0.25

    # combined drift fraction 0..1
    drift_frac = (w_name * d_name) + (w_addr * d_addr) + (w_phone * d_phone)
    drift_percent = round(drift_frac * 100, 2)

    changed = []
    if d_name > 0.1:
        changed.append("name")
    if d_addr > 0.1:
        changed.append("address")
    if d_phone > 0.0:
        # any phone mismatch is important
        changed.append("phone")

    field_diffs = {
        "name_similarity": round(s_name, 3),
        "address_similarity": round(s_addr, 3),
        "phone_match": round(s_phone, 3),
        "name_changed": d_name > 0.1,
        "address_changed": d_addr > 0.1,
        "phone_changed": d_phone > 0.0
    }

    return {
        "drift_score": drift_percent,
        "changed_fields": changed,
        "field_diffs": field_diffs
    }

def record_snapshot(provider_name, snapshot_candidate):
    """
    Record snapshot into history and compute drift against last saved snapshot.
    snapshot_candidate: dict with name,address,phone,website,retrieved_at
    Returns: { history_count, last_snapshot_ts, drift_info, latest_snapshot }
    """
    key = _slug(provider_name)
    hist = load_history()

    if key not in hist:
        hist[key] = {"name": provider_name, "snapshots": []}

    snapshots = hist[key]["snapshots"]

    new_snap = {
        "ts": int(time.time()),
        "candidate": {
            "name": snapshot_candidate.get("name"),
            "address": snapshot_candidate.get("address"),
            "phone": snapshot_candidate.get("phone"),
            "website": snapshot_candidate.get("website"),
            "retrieved_at": snapshot_candidate.get("retrieved_at", int(time.time()))
        }
    }

    drift_info = None
    if snapshots:
        last = snapshots[-1]["candidate"]
        drift_info = compute_drift_score(last, new_snap["candidate"])
    else:
        drift_info = {
            "drift_score": 0.0,
            "changed_fields": [],
            "field_diffs": {
                "name_similarity": 1.0,
                "address_similarity": 1.0,
                "phone_match": 1.0,
                "name_changed": False,
                "address_changed": False,
                "phone_changed": False
            }
        }

    snapshots.append(new_snap)
    hist[key]["snapshots"] = snapshots
    save_history(hist)

    return {
        "history_count": len(snapshots),
        "last_snapshot_ts": snapshots[-1]["ts"],
        "drift_info": drift_info,
        "latest_snapshot": snapshots[-1]["candidate"]
    }
