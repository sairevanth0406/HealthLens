# scraper/real_scraper.py
import requests
from bs4 import BeautifulSoup

def scrape_apollo(query):
    """
    Demo real scraping from Apollo Hospitals 'Contact Us' page.
    (You can replace this with any other public hospital/clinic site)
    """
    url = "https://www.apollohospitals.com/contact-us/"  # Public info page
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract phone numbers (Apollo uses these classes often)
        phones = soup.select('a[href^="tel:"]')
        phone_numbers = [p.text.strip() for p in phones]

        # Extract address (Apollo uses various tags)
        addresses = soup.find_all(['p', 'span'], string=lambda t: t and "Address" in t)

        address = None
        if addresses:
            address = addresses[0].get_text(strip=True)

        return {
            "source": "Apollo Hospitals Website",
            "name": query,
            "address": address,
            "phone": phone_numbers[0] if phone_numbers else None,
            "website": url
        }

    except Exception as e:
        return {"error": str(e)}
