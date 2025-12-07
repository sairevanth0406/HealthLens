# frontend/admin.py
import streamlit as st
import requests

st.set_page_config(page_title="HealthLens Admin", layout="centered")
st.title("HealthLens — Admin Panel")

st.header("Approve Correction")

provider = st.text_input("Provider Name")
corrected_name = st.text_input("Corrected Name (optional)")
corrected_address = st.text_input("Corrected Address")
corrected_phone = st.text_input("Corrected Phone")
accepted_source = st.text_input("Accepted Candidate Source (optional)")   # e.g., "OpenStreetMap Nominatim API"

if st.button("Submit Correction"):
    payload = {
        "provider_name": provider,
        "corrected_name": corrected_name,
        "corrected_address": corrected_address,
        "corrected_phone": corrected_phone,
        "accepted_candidate_source": accepted_source,
        "decision": "approve",
        "admin_user": "admin"
    }

    try:
        r = requests.post("http://localhost:8000/feedback", json=payload)
        st.write(r.json())
    except Exception as e:
        st.error(str(e))


st.header("View History File")
if st.button("Show history.json"):
    try:
        r = requests.get("http://localhost:8000/admin/history")
        st.json(r.json())
    except Exception as e:
        st.error(str(e))
