# scripts/train_entity_model.py
import json, os
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
import joblib
from verification.entity_resolution import build_features, MODEL_PATH

# create training examples from history.json (you must have created history via drift)
HISTORY = os.path.join(os.path.dirname(__file__), "../data/history.json")
if not os.path.exists(HISTORY):
    print("No history.json found. Run your system to gather some snapshots first.")
    exit(0)

hist = json.load(open(HISTORY, "r", encoding="utf-8"))

X = []
y = []
# We will create synthetic labels:
# when snapshot candidate phone==known fallback => label 1 (match)
# else label 0. This is simplistic — you can improve later.
for key, rec in hist.items():
    snaps = rec.get("snapshots", [])
    for s in snaps:
        cand = s.get("candidate", {})
        listed = {"name": rec.get("name"), "listed_phone": cand.get("phone"), "listed_address": cand.get("address")}
        # for training create a positive example by pairing with same candidate (label 1)
        # and a negative example by pairing with a synthetic altered candidate.
        xpos, _, _ = build_features(listed, cand)
        X.append(xpos)
        y.append(1)
        # negative example: change phone or address
        neg = cand.copy()
        neg["phone"] = "9999999999"
        xneg, _, _ = build_features(listed, neg)
        X.append(xneg)
        y.append(0)

X = np.array(X)
y = np.array(y)

model = LogisticRegression(max_iter=500)
model.fit(X, y)
Path(os.path.dirname(MODEL_PATH)).mkdir(parents=True, exist_ok=True)
joblib.dump(model, MODEL_PATH)
print("Saved model to", MODEL_PATH)
