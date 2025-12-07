# verification/confidence.py
import time
from collections import defaultdict
from rapidfuzz import fuzz

# -----------------------------------------
# SOURCE WEIGHTS (YOU CAN TUNE)
# -----------------------------------------
SOURCE_CREDIBILITY = {
    "Public Registry (via Nominatim placeholder)": 1.0,
    "Apollo Hospitals Website": 0.95,
    "Hospital Site 2 (example placeholder)": 0.9,
    "OpenStreetMap Nominatim API": 0.75,
    "example-hospital.com": 0.7,
    "stub": 0.3,
    "Unknown": 0.5
}

SECONDS_IN_DAY = 86400.0

def _source_weight(src):
    return SOURCE_CREDIBILITY.get(src, SOURCE_CREDIBILITY["Unknown"])

def _time_weight(retrieved_at):
    if not retrieved_at:
        return 1.0
    age_seconds = max(0, time.time() - float(retrieved_at))
    age_days = age_seconds / SECONDS_IN_DAY
    return 1.0 / (1.0 + age_days * 0.05)   # slower decay

# -------------------------------------------------
#  FIELD SIMILARITY HELPERS
# -------------------------------------------------
def text_similarity(a, b):
    if not a or not b:
        return 0.0
    try:
        return fuzz.token_sort_ratio(str(a), str(b)) / 100.0
    except:
        return 0.0

def phone_similarity(a, b):
    if not a or not b:
        return 0.0
    na = ''.join(filter(str.isdigit, str(a)))
    nb = ''.join(filter(str.isdigit, str(b)))
    if na == nb and na != "":
        return 1.0
    if len(na) >= 6 and len(nb) >= 6 and na[-6:] == nb[-6:]:
        return 0.8
    return 0.0

# -------------------------------------------------
#   MAIN FIELD SCORE COMPUTATION
# -------------------------------------------------
def compute_field_scores(listed, candidates):

    votes = {
        "name": defaultdict(float),
        "address": defaultdict(float),
        "phone": defaultdict(float),
        "website": defaultdict(float)
    }

    source_votes = {"name": [], "address": [], "phone": [], "website": []}

    # ---- accumulate weighted votes ----
    for c in candidates:
        src = c.get("source", "Unknown")
        weight = _source_weight(src) * _time_weight(c.get("retrieved_at"))

        # NAME
        name_val = c.get("name")
        if name_val:
            votes["name"][name_val] += weight
            source_votes["name"].append((src, name_val, weight))

        # ADDRESS
        addr_val = c.get("address")
        if addr_val:
            votes["address"][addr_val] += weight
            source_votes["address"].append((src, addr_val, weight))

        # PHONE
        phone_val = c.get("phone")
        if phone_val:
            votes["phone"][phone_val] += weight
            source_votes["phone"].append((src, phone_val, weight))

        # WEBSITE
        site_val = c.get("website")
        if site_val:
            votes["website"][site_val] += weight
            source_votes["website"].append((src, site_val, weight))

    # -----------------------------------------
    #  Determine “chosen” consensus values
    # -----------------------------------------
    chosen = {}
    for field in ["name", "address", "phone", "website"]:
        if votes[field]:
            v, w = max(votes[field].items(), key=lambda x: x[1])
            chosen[field] = {"value": v, "weight": w}
        else:
            chosen[field] = {"value": None, "weight": 0}

    # -----------------------------------------
    # FIELD SIMILARITY AGAINST USER INPUT
    # -----------------------------------------
    field_scores = {}

    # NAME similarity
    ln = listed.get("name")
    cn = chosen["name"]["value"]
    field_scores["name"] = text_similarity(ln, cn) if ln and cn else 0.0

    # ADDRESS similarity — treat missing user address as NEUTRAL (0.5)
    la = listed.get("listed_address")
    ca = chosen["address"]["value"]
    if la:
        field_scores["address"] = text_similarity(la, ca) if ca else 0.0
    else:
        field_scores["address"] = 0.5  # neutral score

    # PHONE similarity — treat missing as NEUTRAL (0.5)
    lp = listed.get("listed_phone")
    cp = chosen["phone"]["value"]
    if lp:
        field_scores["phone"] = phone_similarity(lp, cp)
    else:
        field_scores["phone"] = 0.5

    # WEBSITE similarity (optional)
    field_scores["website"] = 0.0

    return chosen, field_scores, source_votes

# -------------------------------------------------
#   CONSENSUS + FINAL SCORING
# -------------------------------------------------
def consensus_score(chosen, field_scores):

    w_name = 0.45
    w_addr = 0.30
    w_phone = 0.20
    w_site = 0.05

    # Weighted field score
    base = (
        w_name * field_scores["name"] +
        w_addr * field_scores["address"] +
        w_phone * field_scores["phone"] +
        w_site * field_scores["website"]
    )

    # Compute consensus boost
    total_w = sum(v["weight"] for v in chosen.values())
    max_w = max((v["weight"] for v in chosen.values()), default=0)

    boost = 0
    if total_w > 0:
        consensus_factor = max_w / total_w  # 0 to 1
        boost = 0.10 * consensus_factor     # up to +0.1

    return min(1.0, base + boost)

# -------------------------------------------------
#   PUBLIC FUNCTION
# -------------------------------------------------
def compute_confidence(listed, candidates):

    chosen, field_scores, source_votes = compute_field_scores(listed, candidates)

    frac = consensus_score(chosen, field_scores)
    final_percent = round(frac * 100, 2)

    flag = final_percent < 70  # threshold

    return {
        "chosen": chosen,
        "field_scores": field_scores,
        "final_confidence": final_percent,
        "flag_for_manual_review": flag,
        "source_votes": source_votes
    }
# at bottom of file
def set_source_credibility(source_name, value):
    """
    Set a new credibility for a source (0..1).
    This does not persist across restarts unless you persist to a file.
    """
    SOURCE_CREDIBILITY[source_name] = float(value)
    return SOURCE_CREDIBILITY[source_name]
