# agents/drift_agent.py
import time
from verification.drift import record_snapshot

class DriftAgent:
    def run(self, provider_name, listed_input):
        snapshot = {
            "name": listed_input["name"],
            "address": listed_input.get("listed_address"),
            "phone": listed_input.get("listed_phone"),
            "website": None,
            "retrieved_at": int(time.time())
        }
        return record_snapshot(provider_name, snapshot)
