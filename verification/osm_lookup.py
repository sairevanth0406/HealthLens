# verification/osm_lookup.py
import requests
import time
def search_osm(query):
    """
    Search OpenStreetMap for a clinic/provider name.
    Returns the first result with address and coordinates.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
        "retrieved_at": time.time()
    }

    headers = {
        "User-Agent": "HealthLens-Demo-App"
    }

    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        if len(data) == 0:
            return None

        item = data[0]
        return {
            "source": "OpenStreetMap Nominatim API",
            "name": item.get("display_name"),
            "address": item.get("display_name"),
            "lat": item.get("lat"),
            "lon": item.get("lon"),
            "retrieved_at": time.time()
        }
    except Exception as e:
        return {"error": str(e)}
