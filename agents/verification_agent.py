# agents/verification_agent.py
from verification.matcher import verify_provider

class VerificationAgent:
    def run(self, listed_input, scraped_candidates):
        return verify_provider(listed_input, scraped_candidates)
