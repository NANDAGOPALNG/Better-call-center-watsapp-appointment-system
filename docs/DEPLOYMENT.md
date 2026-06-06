# Deployment Guide

## Backend on Render

The repository includes `backend/render.yaml`.

1. Push the repository to GitHub.
2. In Render, create a Blueprint and select the repository.
3. Confirm the service root is `backend`.
4. Configure secret environment variables:

```text
SUPABASE_URL
SUPABASE_KEY
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER
TWILIO_WHATSAPP_NUMBER
TWILIO_WHATSAPP_ENABLED
MESSAGING_MODE
GEMINI_API_KEY
GEMINI_MODEL
CORS_ORIGINS=https://your-project.vercel.app
```

Render uses:

```text
Build: pip install -r requirements.txt
Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health: /api/health
```

The APScheduler reminder job runs in the web process. Keep one Render instance
to avoid duplicate reminders. For multiple instances, move reminders to a
dedicated worker with a distributed lock or job queue.

## Frontend on Vercel

1. Import the same GitHub repository into Vercel.
2. Set the root directory to `frontend`.
3. Use the Vite preset.
4. Set:

```text
VITE_API_URL=https://your-render-service.onrender.com
VITE_AI_ENABLED=true
```

5. Deploy.

`frontend/vercel.json` rewrites application routes to `index.html`, so direct
navigation to `/create` works.

## Final CORS Update

After Vercel assigns the production URL, set Render's `CORS_ORIGINS` to that
exact origin. Multiple origins can be comma-separated.

## Production Checklist

- Use the Supabase service-role key only in Render.
- Verify the Twilio Sandbox sender and joined destination number.
- Confirm `/api/health` reports `database: ok` and the intended messaging mode.
- Test a mock or WhatsApp confirmation.
- Create a near-term appointment and verify one reminder.
- Review Render logs for Twilio or Gemini failures.
- Restrict CORS to known frontend origins.
