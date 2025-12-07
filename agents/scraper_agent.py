# agents/scraper_agent.py
import time
from scraper.registry_scraper import scrape_registry
from scraper.hospital_scraper2 import scrape_hospital_2
from scraper.real_scraper import scrape_apollo
from verification.osm_lookup import search_osm
from scraper.phone_sources import match_hospital_key
from scraper.phone_scraper import scrape_phone_from_website

class ScraperAgent:
    def run(self, provider_name: str):
        scraped = []

        # Registry
        reg = scrape_registry(provider_name)
        if reg:
            scraped.append(reg)

        # Hospital Source 2
        h2 = scrape_hospital_2(provider_name)
        if h2:
            scraped.append(h2)

        # OSM lookup
        osm = search_osm(provider_name)
        if osm:
            scraped.append({
                "source": osm["source"],
                "name": provider_name,
                "address": osm["address"],
                "phone": None,
                "website": None,
                "retrieved_at": time.time()
            })

        # Apollo scraper
        ap = scrape_apollo(provider_name)
        if ap and "error" not in ap:
            scraped.append(ap)

        # Phone scraper
        key = match_hospital_key(provider_name)
        if key:
            phone_data = scrape_phone_from_website(provider_name)
            if phone_data:
                scraped.append({
                    "source": phone_data["source"],
                    "name": provider_name,
                    "address": None,
                    "phone": phone_data["phone"],
                    "website": phone_data["website"],
                    "retrieved_at": phone_data["retrieved_at"]
                })

        return scraped
