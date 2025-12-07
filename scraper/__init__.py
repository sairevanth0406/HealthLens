# scraper/__init__.py
# Expose scrapers
from .fetch_provider import fetch as fetch_stub
from .real_scraper import scrape_apollo
from .hospital_scraper2 import scrape_hospital_2
from .registry_scraper import scrape_registry
