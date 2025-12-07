# scraper/fetch_provider.py
import sys, json, os, time

# Demo scraper stub — simulates scraped data
# Later you can replace this with Scrapy, Playwright, API calls, etc.

def fetch(provider_name):
    # pretend these were scraped from real sources like hospital websites or registries
    candidates = [
        {
            "source": "https://example-hospital.com/abc-clinic",
            "name": "ABC Clinic",
            "address": "123 MG Road, City",
            "phone": "+91-9876543210",
            "website": "https://example-hospital.com/abc",
            "retrieved_at": time.time()
        },
        {
            "source": "https://gov-registry.example/abc-clinic",
            "name": "ABC Clinic",
            "address": "123 M.G. Rd, City",
            "phone": "+91-9876543219",
            "website": "https://gov-registry.example/abc",
            "retrieved_at": time.time()
        }
    ]
    return candidates

if __name__ == "__main__":
    # usage: python fetch_provider.py "ABC Clinic"
    provider_name = sys.argv[1] if len(sys.argv) > 1 else "ABC Clinic"
    out = fetch(provider_name)

    data_dir = os.path.join(os.path.dirname(__file__), "../data")
    os.makedirs(data_dir, exist_ok=True)

    outpath = os.path.join(data_dir, "scraped_output.json")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"Scraped candidates written to {outpath}")
