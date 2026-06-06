# Better-call-center-watsapp-appointment-system

A full-stack appointment management system built for call-center operations. The backend exposes a REST API via **FastAPI** backed by **Supabase (PostgreSQL)**, delivers booking confirmations and reminders over **SMS and WhatsApp** through **Twilio**, and optionally generates AI-powered appointment summaries using the **Gemini API**. The frontend is a responsive **React + Vite** dashboard with live analytics.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [1. Database Setup](#1-database-setup)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
  - [4. Verification](#4-verification)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Messaging Modes](#messaging-modes)
- [Deployment](#deployment)
  - [Backend — Render](#backend--render)
  - [Frontend — Vercel](#frontend--vercel)
- [Design Decisions](#design-decisions)
- [Known Limitations](#known-limitations)

---

## Features

- **Full appointment lifecycle** — create, view, update status, and delete appointments.
- **Five-status workflow** — `Scheduled → Confirmed → Reminder Sent → Completed → Cancelled`.
- **Multi-channel messaging** — configurable mock, SMS, WhatsApp, or simultaneous dual-channel delivery via Twilio.
- **Automated reminders** — APScheduler polls every five minutes and sends WhatsApp or SMS reminders to appointments within the next hour.
- **AI appointment summaries** — optional Gemini-powered booking overviews surfaced directly in the dashboard, with a graceful fallback when the key is absent.
- **Live analytics dashboard** — five real-time cards (total, today, confirmed, pending, reminder sent) that auto-refresh every five seconds.
- **Fault-tolerant design** — Twilio and Gemini failures are logged and do not roll back a successfully stored appointment.
- **Interactive API docs** — auto-generated Swagger UI at `/docs` and OpenAPI JSON at `/openapi.json`.
- **One-click deployment** — `render.yaml` for the backend and `vercel.json` for the frontend.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12+, FastAPI, Uvicorn |
| **Database** | Supabase (PostgreSQL) |
| **Messaging** | Twilio (SMS + WhatsApp) |
| **AI Summaries** | Google Gemini API (`gemini-2.5-flash`) |
| **Scheduler** | APScheduler (in-process) |
| **HTTP Client** | httpx |
| **Frontend** | React 18, Vite 6, Tailwind CSS |
| **Routing** | React Router v7 |
| **HTTP (Client)** | Axios |
| **Notifications** | react-hot-toast |
| **Backend Hosting** | Render |
| **Frontend Hosting** | Vercel |

---

## Architecture

```
┌─────────────────────┐        Axios /api/*        ┌─────────────────────────┐
│   React + Vite      │ ─────────────────────────► │   FastAPI (Uvicorn)     │
│   (Vercel)          │                             │   (Render)              │
└─────────────────────┘                             └────────────┬────────────┘
                                                                 │
                     ┌───────────────────────────────────────────┼───────────────────┐
                     │                                           │                   │
                     ▼                                           ▼                   ▼
          ┌─────────────────────┐               ┌────────────────────┐  ┌────────────────────┐
          │  Supabase           │               │  Twilio            │  │  Gemini API        │
          │  (PostgreSQL)       │               │  (SMS / WhatsApp)  │  │  (AI Summaries)    │
          │  appointments       │               └────────────────────┘  └────────────────────┘
          │  message_logs       │
          └─────────────────────┘
                     ▲
                     │ polls every 5 min
          ┌─────────────────────┐
          │  APScheduler        │
          │  (reminder worker)  │
          └─────────────────────┘
```

**Request flow for a new booking:**

1. The React form converts local date/time to an ISO 8601 UTC value before submission.
2. FastAPI validates the phone number (E.164 format) and confirms the appointment time is in the future.
3. An optional Gemini summary is requested; a static fallback is used on failure.
4. The appointment is persisted to Supabase.
5. A confirmation message is dispatched via the configured messaging mode (mock, SMS, WhatsApp, or both).
6. The dashboard polls `/api/appointments` and `/api/analytics/dashboard` every five seconds.
7. APScheduler scans for upcoming appointments every five minutes and sends reminders to those within the next hour.
8. Per-channel delivery flags (`sms_confirmation_sent`, `whatsapp_confirmation_sent`, etc.) prevent duplicate sends on retry.

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   └── main.py            # All routes, models, scheduler, and integrations
│   ├── .env.example           # Required environment variable template
│   ├── render.yaml            # Render deployment blueprint
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/        # Reusable UI: AppointmentForm, AppointmentTable,
│   │   │                      #   DashboardCards, ErrorBoundary, LoadingSpinner, Navbar
│   │   ├── hooks/
│   │   │   └── useAppointments.js   # Dashboard data state and polling logic
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        # Main analytics + appointments view
│   │   │   └── CreateAppointment.jsx
│   │   └── services/
│   │       ├── apiClient.js         # Axios instance and error normalization
│   │       ├── appointmentService.js
│   │       ├── analyticsService.js
│   │       └── healthService.js
│   ├── .env.example
│   ├── vercel.json            # SPA route rewrite rules
│   └── package.json
└── docs/
    ├── API.md
    ├── ARCHITECTURE.md
    ├── DEMO.md
    ├── DEPLOYMENT.md
    └── SETUP.md
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- A [Supabase](https://supabase.com) project
- (Optional) A [Twilio](https://www.twilio.com) trial account for live messaging
- (Optional) A [Google Gemini](https://aistudio.google.com) API key for AI summaries

---

### 1. Database Setup

Run the following SQL in your Supabase project's SQL editor:

```sql
create table if not exists public.appointments (
  id                          bigint generated by default as identity primary key,
  customer_name               text not null,
  phone_number                text not null,
  appointment_time            timestamptz not null,
  purpose                     text not null,
  ai_summary                  text,
  status                      text not null default 'Scheduled'
    check (status in ('Scheduled', 'Confirmed', 'Reminder Sent', 'Completed', 'Cancelled')),
  confirmation_sent           boolean not null default false,
  reminder_sent               boolean not null default false,
  whatsapp_confirmation_sent  boolean not null default false,
  whatsapp_reminder_sent      boolean not null default false,
  created_at                  timestamptz not null default now(),
  updated_at                  timestamptz not null default now()
);

create index if not exists appointments_time_idx
  on public.appointments (appointment_time);

create index if not exists appointments_reminder_idx
  on public.appointments (reminder_sent, appointment_time);

create table if not exists public.message_logs (
  id              bigint generated by default as identity primary key,
  appointment_id  bigint not null references public.appointments(id) on delete cascade,
  message_type    text not null check (message_type in ('confirmation', 'reminder')),
  channel         text not null check (channel in ('mock', 'sms', 'whatsapp')),
  recipient       text not null,
  body            text not null,
  status          text not null check (status in ('sent', 'failed')),
  provider_id     text,
  created_at      timestamptz not null default now()
);

create index if not exists message_logs_appointment_idx
  on public.message_logs (appointment_id, created_at desc);
```

> **Migrating an existing table?** Add only the WhatsApp tracking columns:
> ```sql
> alter table public.appointments
>   add column if not exists whatsapp_confirmation_sent boolean not null default false,
>   add column if not exists whatsapp_reminder_sent     boolean not null default false;
> ```
> Restart the backend after the migration — schema capability checks are cached for the process lifetime.

---

### 2. Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials (see Environment Variables below)

# Start the API server
uvicorn app.main:app --reload --port 8000
```

Set `MESSAGING_MODE=mock` during local development to avoid consuming Twilio trial credits.

---

### 3. Frontend Setup

```bash
cd frontend

# Configure environment
cp .env.example .env
# Edit .env:
#   VITE_API_URL=http://localhost:8000
#   VITE_AI_ENABLED=true

npm install
npm run dev
```

---

### 4. Verification

| Endpoint | Expected |
|---|---|
| `http://localhost:5173` | React dashboard |
| `http://localhost:8000/api/health` | JSON with service statuses |
| `http://localhost:8000/docs` | Swagger UI |
| `http://localhost:8000/openapi.json` | OpenAPI schema |

Create a test appointment at least a few minutes in the future using an E.164 phone number (e.g. `+15551234567`). In mock mode the confirmation is logged to console and written to `message_logs`; no real message is sent.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase service-role key (never expose client-side) |
| `MESSAGING_MODE` | ✅ | `mock`, `sms`, `whatsapp`, or `both` |
| `CORS_ORIGINS` | ✅ | Comma-separated list of allowed frontend origins |
| `TWILIO_ACCOUNT_SID` | Twilio only | Account identifier |
| `TWILIO_AUTH_TOKEN` | Twilio only | Account secret |
| `TWILIO_PHONE_NUMBER` | SMS mode | Sender number in E.164 format |
| `TWILIO_WHATSAPP_NUMBER` | WhatsApp mode | Sandbox sender in E.164 format |
| `TWILIO_WHATSAPP_ENABLED` | No | Set `true` to enable WhatsApp delivery |
| `GEMINI_API_KEY` | No | Enables AI appointment summaries |
| `GEMINI_MODEL` | No | Defaults to `gemini-2.5-flash` |

### Frontend (`frontend/.env`)

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend base URL (e.g. `http://localhost:8000`) |
| `VITE_AI_ENABLED` | Set `false` to suppress AI summary requests from the form |

---

## API Reference

Full interactive documentation is available at `/docs`. A summary of all endpoints:

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/appointments` | Create an appointment; triggers confirmation delivery |
| `GET` | `/api/appointments` | List all appointments ordered by time |
| `GET` | `/api/appointments/{id}` | Retrieve a single appointment |
| `PATCH` | `/api/appointments/{id}/status` | Update appointment status |
| `DELETE` | `/api/appointments/{id}` | Delete an appointment |
| `GET` | `/api/analytics/dashboard` | Return dashboard aggregate counts |
| `POST` | `/api/ai/summary` | Generate an AI summary or return fallback text |
| `GET` | `/api/health` | Report API, database, messaging, and AI service status |

**Create appointment request body:**

```json
{
  "customer_name": "Taylor Smith",
  "phone_number": "+15551234567",
  "appointment_time": "2026-06-07T10:30:00Z",
  "purpose": "Discuss plan upgrade options"
}
```

**Update status request body:**

```json
{ "status": "Confirmed" }
```

Valid status values: `Scheduled`, `Confirmed`, `Reminder Sent`, `Completed`, `Cancelled`.

**Analytics response:**

```json
{
  "total": 18,
  "today": 4,
  "confirmed": 7,
  "pending": 5,
  "reminder_sent": 9
}
```

**Error codes:** `400` validation error · `404` record not found · `503` database not configured · `500` unexpected database failure.

Pass `X-AI-Enabled: false` on any request to skip Gemini summary generation for that call.

---

## Messaging Modes

| Mode | Behavior |
|---|---|
| `mock` | No external request is made. The message body is logged to console and written to `message_logs` in Supabase. |
| `sms` | Message delivered via Twilio SMS only. |
| `whatsapp` | Message delivered via Twilio WhatsApp Sandbox (or approved sender). |
| `both` | Both channels are attempted. If one channel fails, only that channel is retried on the next scheduler pass; a successful channel is not re-sent. |

**WhatsApp Sandbox setup (free testing):**

1. Open the Twilio Console → Messaging → Try it Out → Send a WhatsApp message.
2. Send the displayed `join <code>` message from the target WhatsApp number.
3. Set `MESSAGING_MODE=whatsapp` and `TWILIO_WHATSAPP_NUMBER` to the sandbox number.
4. Create appointments using that same WhatsApp-joined phone number.

> Production business-initiated WhatsApp reminders require an approved WhatsApp Business sender and pre-approved message templates.

---

## Deployment

### Backend — Render

The repo includes `backend/render.yaml` for a one-click Blueprint deploy.

1. Push the repository to GitHub.
2. In Render, create a new **Blueprint** and select the repository.
3. Confirm the service root directory is `backend`.
4. Add the following secret environment variables in the Render dashboard:

```
SUPABASE_URL
SUPABASE_KEY
MESSAGING_MODE
CORS_ORIGINS=https://your-project.vercel.app
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER
TWILIO_WHATSAPP_NUMBER
TWILIO_WHATSAPP_ENABLED
GEMINI_API_KEY
GEMINI_MODEL
```

Render runs:
- **Build:** `pip install -r requirements.txt`
- **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health check:** `GET /api/health`

> ⚠️ The APScheduler reminder job runs inside the web process. Keep the backend at **one instance** to prevent duplicate reminders. For multi-instance deployments, move the reminder job to a dedicated worker with a distributed lock or a job queue.

---

### Frontend — Vercel

1. Import the same GitHub repository into Vercel.
2. Set the **Root Directory** to `frontend`.
3. Select the **Vite** framework preset.
4. Set environment variables:
   ```
   VITE_API_URL=https://your-render-service.onrender.com
   VITE_AI_ENABLED=true
   ```
5. Deploy.

`frontend/vercel.json` rewrites all application routes to `index.html`, so deep links such as `/create` work correctly on direct navigation.

After Vercel assigns your production URL, update `CORS_ORIGINS` on Render to that exact origin.

**Production checklist:**

- [ ] Supabase service-role key is set only in Render (never in a `VITE_` variable).
- [ ] `/api/health` reports `database: ok` and the expected messaging mode.
- [ ] A mock or WhatsApp confirmation can be triggered successfully.
- [ ] A near-term appointment triggers a reminder within the next scheduler cycle.
- [ ] Render logs are reviewed for Twilio or Gemini errors.
- [ ] `CORS_ORIGINS` is restricted to known frontend origins only.

---

## Design Decisions

**Database as source of truth.** Twilio and Gemini calls are best-effort integrations. A failure in either does not roll back a successfully created appointment; it is logged and retried on the next scheduler pass or next request.

**Per-channel delivery flags.** Separate boolean columns (`sms_confirmation_sent`, `whatsapp_confirmation_sent`, etc.) allow `both` mode to retry only the channel that failed without re-sending the successful one. A backwards-compatible fallback uses the generic flags when the WhatsApp columns are absent (pre-migration tables).

**In-process scheduler.** APScheduler runs inside the Uvicorn process for simplicity. This is appropriate for a single-instance deployment; a distributed lock or external queue (e.g. Celery + Redis) would be required before horizontal scaling.

**Frontend UTC conversion.** The React form converts the user's local date/time to UTC before sending it to the API. This avoids timezone ambiguity at the persistence layer and means all stored times are unambiguous regardless of where the call-center agent is located.

**Optional AI with non-blocking fallback.** Gemini summary generation is wrapped in a try/except. If the API key is absent or the call fails, the appointment is stored with the static string `"AI summary not configured"` — the booking is never blocked by an AI service outage.

---

## Known Limitations

- The in-process APScheduler reminder job means reminders will not fire during a Render cold start or service restart. Running more than one backend instance will cause duplicate reminders.
- Twilio trial accounts can only send SMS to verified phone numbers. WhatsApp Sandbox messages can only reach numbers that have joined the sandbox.
- Production WhatsApp messaging requires an approved WhatsApp Business sender and pre-approved content templates — the Sandbox is for development only.
- The `lru_cache` on the WhatsApp column capability check is per-process. A schema migration requires a backend restart to take effect.
