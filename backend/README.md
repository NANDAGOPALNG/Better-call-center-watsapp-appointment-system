# Backend

FastAPI service for appointment CRUD, analytics, health checks, Twilio SMS and
WhatsApp delivery, mock messaging, and optional Gemini summaries.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

See the root [setup guide](../docs/SETUP.md) for database SQL and environment
variables. Interactive API documentation is available at `/docs`.
