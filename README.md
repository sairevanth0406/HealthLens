🎯 HealthLens — AI-Powered Healthcare Provider Verification System
A Smart, Automated, Multi-Agent System to Validate & Clean Healthcare Provider Data

LIVE WEBSITE : https://healthlens-frontend.onrender.com

🚀 Overview

Healthcare provider directories are often inaccurate — wrong phone numbers, outdated addresses, clinics that have shifted, or doctors no longer practicing.
Over 80% of healthcare listings contain errors, leading to:

❌ Patient frustration

❌ Lost appointments

❌ Insurance compliance risks

❌ Huge manual verification overhead

HealthLens solves this using a multi-agent AI pipeline that automatically validates and updates provider information across:

Hospital websites

Public registries

OpenStreetMap

Known hospital databases

Phone/contact extraction systems

🎯 Goal: Ensure clean, accurate, trustworthy provider data using automation + intelligence.

🧠 Key Features
✅ Multi-Agent AI Pipeline
Agent	Role
🛰 Scraper Agent	Fetches provider info from multiple trusted sources
🔍 Verification Agent	Performs fuzzy matching, similarity scoring, and consensus building
📡 OSM Agent	Cross-checks address using OpenStreetMap API
📞 Phone Extraction Agent	Extracts, validates, normalizes phone numbers
⚠️ Drift Agent	Detects changes between real-world info & directory data
🧬 Entity Resolution Agent	Final decision-making & confidence scoring
🏥 Why HealthLens? (Problem Solved)

Healthcare directories fail due to:

Outdated provider data

Manual verification burden

No automation

No feedback loops

No source reliability measurement

HealthLens automates all of it:

AI-powered provider validation

Multi-source consensus scoring

Field-level confidence breakdown

Drift detection

Feedback loop for continuous learning

Admin correction system

Secure login + user history tracking

<img width="672" height="1380" alt="_- visual selection (22)" src="https://github.com/user-attachments/assets/831d7442-e876-48d0-966e-222d6ae82627" />


🧩 Core Modules
🔹 1. Scraper Engine

Registry scraper

Hospital site scrapers

Apollo/Yashoda/AIG scrapers

OpenStreetMap integration

Phone extraction

🔹 2. Entity Resolution

RapidFuzz similarity scoring

Name match

Address match

Phone match

Weighted consensus

🔹 3. Drift Detection

Detects when user-entered data differs from real-world data

Tracks history

Computes drift score

Highlights changed fields

🔹 4. Feedback Loop

Admin approves/rejects candidate info

System updates source credibility

Learns over time

🌐 Frontend (Flask UI)
🟩 Features:

Clean healthcare-themed UI

Login & Signup

Role-based Access (User / Admin)

Provider verification page

Search history dashboard

Admin correction panel

Logout + persistent session

💾 Search History & User System

All searches store:

Username

Provider queried

User-entered fields

Returned confidence score

Drift info

Timestamp

Admins can view all histories; users only view their own.

🧪 Sample Output Snapshot
✔ Confidence Scoring
{
  "confidence": 85.77,
  "name_similarity": 1.0,
  "address_similarity": 0.62,
  "phone_match": 1.0,
  "flag_for_manual_review": false
}

✔ Drift Detection
{
  "drift_score": 46.54,
  "changed_fields": ["address", "phone"],
  "history_count": 14
}

🚧 Tech Stack
Backend

FastAPI

Python Scrapers

Multi-Agent Orchestration

OpenStreetMap API

RapidFuzz (Entity Resolution)

Frontend

Flask

Bootstrap 5

Jinja Templates

Data Layer

Local JSON (Demo)

Pluggable to SQL/NoSQL

🔐 Authentication

User / Admin separation

Each user has personal search history

▶️ How to Run
1️⃣ Start Backend
uvicorn api.main:app --reload --port 8000

2️⃣ Start Frontend
cd frontend_flask
python app.py



🏁 Future Enhancements

LLM-powered provider name normalization

Multi-language support

Automated periodic scraping

Integration with insurance APIs

Elasticsearch search engine

OAuth login
