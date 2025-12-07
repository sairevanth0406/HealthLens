# verification/matcher.py
import json, os
from rapidfuzz import fuzz
from .confidence import compute_confidence
import time

def load_scraped(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "../data/scraped_output.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Keep a backward-compatible simple verify function that now delegates to compute_confidence
def verify_provider(listed, scraped_list):
    """
    listed: dict with keys name, listed_phone, listed_address (coming from user / directory)
    scraped_list: list of candidate dicts (source,name,address,phone,website,retrieved_at)
    """
    # Ensure all candidates have retrieved_at (if missing, set to now - 7 days)
    now = time.time()
    for c in scraped_list:
        if "retrieved_at" not in c or c.get("retrieved_at") is None:
            # assume older candidate — set retrieved_at to 7 days ago
            c["retrieved_at"] = now - 7 * 86400

    # call new confidence engine
    result = compute_confidence(listed, scraped_list)

    # Also attach top candidate info (the chosen per field combined)
    chosen = result.get("chosen", {})
    # build a top candidate summary by selecting chosen values:
    top_candidate = {
        "source": "consensus",
        "name": chosen["name"]["value"],
        "address": chosen["address"]["value"],
        "phone": chosen["phone"]["value"],
        "website": chosen["website"]["value"]
    }
    result["candidate"] = top_candidate
    return result
