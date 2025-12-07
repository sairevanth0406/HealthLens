# agents/controller_agent.py
from agents.scraper_agent import ScraperAgent
from agents.verification_agent import VerificationAgent
from agents.drift_agent import DriftAgent

class ControllerAgent:
    def __init__(self):
        self.scraper = ScraperAgent()
        self.verifier = VerificationAgent()
        self.drift = DriftAgent()

    def run(self, provider_input):
        name = provider_input["name"]

        # 1. Scraper agent
        scraped = self.scraper.run(name)

        # 2. Verification agent
        verification_result = self.verifier.run(provider_input, scraped)

        # 3. Drift agent
        drift_result = self.drift.run(name, provider_input)

        # Final combined response
        verification_result["drift"] = drift_result
        return verification_result
