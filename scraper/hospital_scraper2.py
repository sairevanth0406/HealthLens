# scraper/hospital_scraper2.py
import requests
from bs4 import BeautifulSoup
import time

def scrape_hospital_2(query):
    """
    Demo scraper for a second hospital source (generic).
    Replace `url` with a real hospital/clinic contact page for better results.
    """
    try:
        # Example public contact page (placeholder) — replace with a stable URL you want to target
        url = "https://www.example-hospital.org/contact-us/"  # <-- replace with real site if you have
        headers = {"User-Agent": "HealthLens-RealScraper2"}
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Attempt to find phone(s) and address (generic selectors)
        phone = None
        phone_el = soup.select_one('a[href^="tel:"]')
        if phone_el:
            phone = phone_el.get_text(strip=True)

        address = None
        # try common address-bearing selectors
        addr_el = soup.select_one(".address") or soup.select_one("#address") or soup.find("address")
        if addr_el:
            address = addr_el.get_text(" ", strip=True)

        candidate = {
            "source": "Hospital Site 2 (example placeholder)",
            "name": query,
            "address": address,
            "phone": phone,
            "website": url,
            "retrieved_at": time.time()
        }
        return candidate
    except Exception:
        return None
