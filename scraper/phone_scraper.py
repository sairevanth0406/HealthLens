# scraper/phone_scraper.py

import requests
from bs4 import BeautifulSoup
import re
import time
from .phone_sources import KNOWN_PHONE_NUMBERS, HOSPITAL_PHONE_PAGES, match_hospital_key

# Strict Indian phone number regex
PHONE_REGEX = r"(\+91[-\s]?\d{10}|0\d{2,4}[-\s]?\d{6,8}|1800[-\s]?\d{3}[-\s]?\d{4})"


def normalize_phone(p):
    """Validate and normalize Indian phone numbers."""
    p = re.sub(r"[^\d+]", "", p)

    # Mobile numbers: start with 6,7,8,9
    if len(p) == 10 and p[0] in "6789":
        return p

    # +91XXXXXXXXXX
    if p.startswith("+91") and len(p) == 13:
        return p

    # Landlines (STD codes)
    valid_std_codes = ["040", "044", "022", "080", "011", "020", "033"]
    if p.startswith("0") and len(p) in (10, 11) and p[:3] in valid_std_codes:
        return p

    # Toll-free
    if p.startswith("1800") and len(p) >= 11:
        return p[:11]

    return None


def extract_phone_from_html(html):
    """Extract phone numbers only from visible text."""
    soup = BeautifulSoup(html, "html.parser")
    phones = set()

    # tel: links (highest priority)
    for tag in soup.select('a[href^="tel:"]'):
        raw = tag.get("href", "")[4:]
        p = normalize_phone(raw)
        if p:
            phones.add(p)

    # visible text regex
    text = soup.get_text(" ", strip=True)
    matches = re.findall(PHONE_REGEX, text)
    for m in matches:
        p = normalize_phone(m)
        if p:
            phones.add(p)

    return list(phones) if phones else None


def scrape_phone_from_website(name):
    """Scrape phone number OR return known fallback number."""
    key = match_hospital_key(name)
    if not key:
        return None  # unknown hospital

    # Pick contact page URL
    url = HOSPITAL_PHONE_PAGES.get(key)

    # -----------------------------------------------------
    # 1️⃣ ALWAYS return official fallback phone number first
    # -----------------------------------------------------
    known = KNOWN_PHONE_NUMBERS.get(key)
    if known:
        return {
            "source": "Official Known Number",
            "phone": known[0],
            "website": url,
            "retrieved_at": time.time()
        }

    # -----------------------------------------------------
    # 2️⃣ Otherwise try scraping the website
    # -----------------------------------------------------
    try:
        resp = requests.get(url, headers={"User-Agent": "HealthLens-PhoneScraper"}, timeout=5)
        resp.raise_for_status()

        phones = extract_phone_from_html(resp.text)
        if phones:
            return {
                "source": "Hospital Website Phone Extractor",
                "phone": phones[0],
                "website": url,
                "retrieved_at": time.time()
            }

    except Exception:
        pass

    return None
