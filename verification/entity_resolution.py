# verification/entity_resolution.py
import os
import time
import json
from pathlib import Path
from rapidfuzz import fuzz
import numpy as np

# Optional ML dependencies; only required if you train/predict a model
# pip install scikit-learn joblib
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    import joblib
    SKL_AVAILABLE = True
except Exception:
    SKL_AVAILABLE = False

# utils copied/consistent with confidence engine
def text_similarity(a, b):
    if not a or not b:
        return 0.0
    return fuzz.token_sort_ratio(str(a), str(b)) / 100.0

def phone_similarity(a, b):
    if not a or not b:
        return 0.0
    na = ''.join(filter(str.isdigit, str(a)))
    nb = ''.join(filter(str.isdigit, str(b)))
    if na == nb and na != "":
        return 1.0
    if na and nb and na[-6:] == nb[-6:]:
        return 0.8
    return 0.0

# Default source credibility (will be read from confidence module if available)
DEFAULT_SOURCE_CRED = {
    "Public Registry (via Nominatim placeholder)": 1.0,
    "Apollo Hospitals Website": 0.95,
    "OpenStreetMap Nominatim API": 0.7,
    "example-hospital.com": 0.75,
    "stub": 0.6,
    "Unknown": 0.5
}

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../models/entity_model.joblib")
HISTORY_PATH = os.path.join(os.path.dirname(__file__), "../data/history.json")

def _get_source_weight(source, source_weights=None):
    if source_weights and source in source_weights:
        return source_weights[source]
    return DEFAULT_SOURCE_CRED.get(source, DEFAULT_SOURCE_CRED["Unknown"])

def features_from_candidate(listed, candidate, source_weights=None):
    # returns numeric feature vector describing how candidate matches listed record
    f_name = text_similarity(listed.get("name"), candidate.get("name"))
    f_addr = text_similarity(listed.get("listed_address"), candidate.get("address"))
    f_phone = phone_similarity(listed.get("listed_phone"), candidate.get("phone"))
    f_source = _get_source_weight(candidate.get("source"), source_weights)
    f_len_name = len(str(candidate.get("name") or "")) / 100.0
    # consensus proxies: not available here, set to 0.5 default
    f_consensus = 0.5
    return [f_name, f_addr, f_phone, f_source, f_len_name, f_consensus]

def resolve_entity(listed, candidates, source_weights=None, use_ml=False):
    """
    Primary resolver. If use_ml=True and model is available, uses the ML model to score.
    Otherwise uses weighted rule-based scoring similar to your consensus_score.
    Returns:
      - best_candidate (dict)
      - scores (dict) per field
      - overall_confidence (0..100)
      - ml_score (if applicable)
    """
    if not candidates:
        return None, {}, 0.0, None

    # Build votes & choose best (weighted by source weight & fuzz)
    candidate_scores = []
    for c in candidates:
        feats = features_from_candidate(listed, c, source_weights)
        # Simple rule-based final score:
        # weighted sum of name(0.4), address(0.35), phone(0.2), source(0.05)
        w_name, w_addr, w_phone, w_src = 0.4, 0.35, 0.2, 0.05
        rule_score = (w_name * feats[0]) + (w_addr * feats[1]) + (w_phone * feats[2]) + (w_src * feats[3])
        candidate_scores.append((c, rule_score, feats))

    # choose max rule_score candidate
    best, best_score, best_feats = max(candidate_scores, key=lambda t: t[1])

    # If ML requested and model exists, compute ml_score
    ml_score = None
    if use_ml and SKL_AVAILABLE and Path(MODEL_PATH).exists():
        model = joblib.load(MODEL_PATH)
        X = np.array([best_feats])
        prob = model.predict_proba(X)[0][1]  # probability of match label 1
        ml_score = float(prob)
        # combine: simple average of rule_score and ml_score
        final_frac = (best_score + ml_score) / 2.0
    else:
        final_frac = best_score

    final_percent = round(max(0.0, min(1.0, final_frac)) * 100, 2)

    field_scores = {
        "name": best_feats[0],
        "address": best_feats[1],
        "phone": best_feats[2],
        "source_weight": best_feats[3]
    }

    return best, field_scores, final_percent, ml_score

# Optional small trainer to create a logistic regression model from history
def train_ml_model(history_path=HISTORY_PATH, outpath=MODEL_PATH):
    """
    Train a small classifier using history.json snapshots.
    Labeling heuristic (quick):
     - If a snapshot later had a correction that matched candidate -> label 1 else 0
    This is a lightweight example to be improved with real labeled data.
    """
    if not SKL_AVAILABLE:
        raise RuntimeError("scikit-learn + joblib required to train model")

    if not os.path.exists(history_path):
        raise FileNotFoundError("history.json not found for training")

    with open(history_path, "r", encoding="utf-8") as f:
        hist = json.load(f)

    X = []
    y = []
    # Very simple approach: for any provider with >=2 snapshots, compute pairwise diffs
    for key, v in hist.items():
        snaps = v.get("snapshots", [])
        for i in range(len(snaps)-1):
            old = snaps[i]["candidate"]
            new = snaps[i+1]["candidate"]
            feats = [
                text_similarity(old.get("name"), new.get("name")),
                text_similarity(old.get("address"), new.get("address")),
                phone_similarity(old.get("phone"), new.get("phone")),
                0.5
            ]
            # label: if new==old (no change) -> label 1 (match), else 0 (changed)
            label = 1 if (feats[0] > 0.95 and feats[1] > 0.95 and feats[2] == 1.0) else 0
            X.append(feats)
            y.append(label)

    if not X:
        raise RuntimeError("Not enough data to train model")

    X = np.array(X)
    y = np.array(y)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    joblib.dump(model, outpath)
    return {"trained": True, "outpath": outpath}
