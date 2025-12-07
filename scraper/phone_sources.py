# scraper/phone_sources.py

# Known verified phone numbers (manual curated)
# These DO NOT change and guarantee stable results.
KNOWN_PHONE_NUMBERS = {
    "basavatarakam": [
        "04023552337",
        "18004253424"
    ],
    "continental": [
        "04067000000"
    ],
    "apollo": [
        "18605001066"
    ],
    "aig": [
        "04042440000"
    ],
    "yashoda": [
        "04045674567"
    ],
    "rainbow": [
        "04044244444"
    ]
}

# Mapping hospital names to contact-page URLs
HOSPITAL_PHONE_PAGES = {
    "basavatarakam": "https://induscancer.com/contact/",
    "continental": "https://continentalhospitals.com/contact-us/",
    "apollo": "https://www.apollohospitals.com/contact-us/",
    "aig": "https://aighospitals.com/contact-us/",
    "yashoda": "https://www.yashodahospitals.com/contact-us/",
    "rainbow": "https://www.rainbowhospitals.in/contact-us"
}

def match_hospital_key(name):
    name = name.lower()
    for key in KNOWN_PHONE_NUMBERS.keys():
        if key in name:
            return key
    return None

