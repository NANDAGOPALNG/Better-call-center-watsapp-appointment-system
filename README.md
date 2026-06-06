# AI-Powered Appointment Automation System

A production-oriented appointment dashboard built from the Better Call Centers
spec. FastAPI and Supabase manage appointments, Twilio sends SMS or WhatsApp
confirmations and reminders, and an optional Gemini summary gives call-center staff a concise
booking overview.

## Features

- Create, list, inspect, update, and delete appointments.
- Responsive dashboard with five live analytics cards.
- Status workflow: Scheduled, Confirmed, Reminder Sent, Completed, Cancelled.
- Configurable mock, SMS, WhatsApp, or dual-channel delivery.
- Confirmation messages after booking and reminders within one hour.
- Optional AI summary with a non-blocking fallback.
- Five-second frontend refresh plus manual refresh.
- FastAPI health endpoint and interactive OpenAPI docs.
- Render and Vercel deployment configuration.

## Project Structure

```text
backend/
  app/main.py
  .env.example
  render.yaml
  requirements.txt
frontend/
  src/
    components/
    hooks/
    pages/
    services/
  .env.example
  vercel.json
docs/
  API.md
  ARCHITECTURE.md
  DEMO.md
  DEPLOYMENT.md
  SETUP.md
```

## Quick Start

1. Create the Supabase table using the SQL in [docs/SETUP.md](docs/SETUP.md).
2. Copy `backend/.env.example` to `backend/.env` and fill in credentials.
3. Copy `frontend/.env.example` to `frontend/.env`.
4. Start the API:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

5. Start the frontend in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. API docs are at
`http://localhost:8000/docs`.

## Documentation

- [Local setup](docs/SETUP.md)
- [Deployment](docs/DEPLOYMENT.md)
- [API summary](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [10-step demo flow](docs/DEMO.md)

## Reliability Notes

Twilio and Gemini errors are logged but do not roll back a successfully stored
appointment. The reminder scheduler runs inside the API process; deploy one
backend instance, or move reminder execution to a dedicated worker before
scaling horizontally.
