import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import List, Optional

import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import Client as SupabaseClient
from supabase import create_client
from twilio.rest import Client as TwilioClient

load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

VALID_STATUSES = {
    "Scheduled",
    "Confirmed",
    "Reminder Sent",
    "Completed",
    "Cancelled",
}
DEFAULT_AI_SUMMARY = "AI summary not configured"
VALID_MESSAGING_MODES = {"mock", "sms", "whatsapp", "both"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def parse_database_datetime(value: str) -> datetime:
    return normalize_datetime(datetime.fromisoformat(value.replace("Z", "+00:00")))


def normalize_appointment_record(record: dict) -> dict:
    normalized = dict(record)
    normalized.setdefault("whatsapp_confirmation_sent", False)
    normalized.setdefault("whatsapp_reminder_sent", False)
    if not supports_whatsapp_columns() and get_messaging_mode() in {
        "whatsapp",
        "both",
    }:
        normalized["whatsapp_confirmation_sent"] = bool(
            normalized.get("confirmation_sent")
        )
        normalized["whatsapp_reminder_sent"] = bool(normalized.get("reminder_sent"))
    return normalized


def get_supabase() -> SupabaseClient:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        )
    return create_client(url, key)


def get_twilio_client() -> Optional[TwilioClient]:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        return None
    return TwilioClient(account_sid, auth_token)


@lru_cache(maxsize=1)
def supports_whatsapp_columns() -> bool:
    try:
        (
            get_supabase()
            .table("appointments")
            .select("id,whatsapp_confirmation_sent,whatsapp_reminder_sent")
            .limit(1)
            .execute()
        )
        return True
    except Exception:
        logger.warning(
            "WhatsApp tracking columns are unavailable; using generic delivery flags"
        )
        return False


def get_messaging_mode() -> str:
    mode = os.getenv("MESSAGING_MODE", "mock").strip().lower()
    if mode not in VALID_MESSAGING_MODES:
        logger.warning("Invalid MESSAGING_MODE=%s; falling back to mock", mode)
        return "mock"
    return mode


def required_channels(mode: Optional[str] = None) -> List[str]:
    selected_mode = mode or get_messaging_mode()
    if selected_mode == "both":
        return ["sms", "whatsapp"]
    return [selected_mode]


def env_enabled(name: str, default: bool = True) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class AppointmentCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    phone_number: str = Field(min_length=10, max_length=20)
    appointment_time: datetime
    purpose: str = Field(min_length=1, max_length=1000)


class AppointmentResponse(AppointmentCreate):
    id: int
    ai_summary: Optional[str] = None
    status: str
    confirmation_sent: bool = False
    reminder_sent: bool = False
    whatsapp_confirmation_sent: bool = False
    whatsapp_reminder_sent: bool = False
    created_at: datetime


class StatusUpdate(BaseModel):
    status: str


class AISummaryRequest(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    appointment_time: datetime
    purpose: str = Field(min_length=1, max_length=1000)


class AISummaryResponse(BaseModel):
    summary: str
    configured: bool


async def generate_ai_summary(appt: AISummaryRequest) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return DEFAULT_AI_SUMMARY

    prompt = (
        "Write one concise sentence for call-center staff summarizing this "
        "appointment. Include the customer, purpose, and appointment time. "
        "Do not invent details.\n"
        f"Customer: {appt.customer_name}\n"
        f"Purpose: {appt.purpose}\n"
        f"Appointment time: {normalize_datetime(appt.appointment_time).isoformat()}"
    )
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 100,
            "temperature": 0.2,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            candidates = response.json().get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                summary = " ".join(
                    part["text"].strip()
                    for part in parts
                    if part.get("text")
                ).strip()
                if summary:
                    return summary
    except Exception:
        logger.exception("Gemini summary generation failed")

    return "AI summary unavailable"


def send_twilio_message(to: str, body: str, channel: str) -> Optional[str]:
    client = get_twilio_client()
    if channel == "whatsapp":
        from_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        if not env_enabled("TWILIO_WHATSAPP_ENABLED"):
            logger.warning("WhatsApp skipped because it is disabled")
            return None
        from_address = f"whatsapp:{from_number}" if from_number else None
        to_address = f"whatsapp:{to}"
    else:
        from_address = os.getenv("TWILIO_PHONE_NUMBER")
        to_address = to

    if channel not in {"sms", "whatsapp"}:
        raise ValueError(f"Unsupported Twilio channel: {channel}")

    if not client or not from_address:
        logger.warning("%s skipped because Twilio is not configured", channel.upper())
        return None

    try:
        message = client.messages.create(
            body=body,
            from_=from_address,
            to=to_address,
        )
        return message.sid
    except Exception:
        logger.exception("%s delivery failed for %s", channel.upper(), to)
        return None


def log_message(
    database: SupabaseClient,
    appointment_id: int,
    message_type: str,
    channel: str,
    recipient: str,
    body: str,
    status_value: str,
    provider_id: Optional[str] = None,
) -> None:
    try:
        database.table("message_logs").insert(
            {
                "appointment_id": appointment_id,
                "message_type": message_type,
                "channel": channel,
                "recipient": recipient,
                "body": body,
                "status": status_value,
                "provider_id": provider_id,
            }
        ).execute()
    except Exception:
        logger.warning(
            "Could not persist message log. Create the optional message_logs table.",
            exc_info=True,
        )


def dispatch_message(
    database: SupabaseClient,
    appointment: dict,
    message_type: str,
    body: str,
) -> dict:
    mode = get_messaging_mode()
    channels = required_channels(mode)
    results = {}
    has_whatsapp_columns = supports_whatsapp_columns()

    for channel in channels:
        flag = (
            "whatsapp_confirmation_sent"
            if channel == "whatsapp"
            and has_whatsapp_columns
            and message_type == "confirmation"
            else "whatsapp_reminder_sent"
            if channel == "whatsapp" and has_whatsapp_columns
            else "confirmation_sent"
            if message_type == "confirmation"
            else "reminder_sent"
        )

        if channel != "mock" and appointment.get(flag):
            results[channel] = True
            continue

        if channel == "mock":
            logger.info(
                "MOCK %s to %s: %s",
                message_type,
                appointment["phone_number"],
                body,
            )
            provider_id = f"mock-{appointment['id']}-{message_type}"
            delivered = True
        else:
            provider_id = send_twilio_message(
                appointment["phone_number"],
                body,
                channel,
            )
            delivered = bool(provider_id)

        results[channel] = delivered
        log_message(
            database=database,
            appointment_id=appointment["id"],
            message_type=message_type,
            channel=channel,
            recipient=appointment["phone_number"],
            body=body,
            status_value="sent" if delivered else "failed",
            provider_id=provider_id,
        )

    return results


def delivery_updates(message_type: str, results: dict) -> dict:
    updates = {"updated_at": utc_now().isoformat()}
    has_whatsapp_columns = supports_whatsapp_columns()
    complete = all(results.values()) if results else False
    if has_whatsapp_columns:
        if results.get("sms"):
            updates[
                "confirmation_sent"
                if message_type == "confirmation"
                else "reminder_sent"
            ] = True
        if results.get("whatsapp"):
            updates[
                "whatsapp_confirmation_sent"
                if message_type == "confirmation"
                else "whatsapp_reminder_sent"
            ] = True
    elif complete:
        updates[
            "confirmation_sent" if message_type == "confirmation" else "reminder_sent"
        ] = True

    if get_messaging_mode() == "mock" and complete:
        updates[
            "confirmation_sent" if message_type == "confirmation" else "reminder_sent"
        ] = True
    if message_type == "reminder" and complete:
        updates["status"] = "Reminder Sent"
    return updates


def check_reminders() -> None:
    try:
        database = get_supabase()
        now = utc_now()
        next_hour = now + timedelta(hours=1)
        query = database.table("appointments").select("*")
        mode = get_messaging_mode()
        if mode == "whatsapp" and supports_whatsapp_columns():
            query = query.eq("whatsapp_reminder_sent", False)
        elif mode == "both" and supports_whatsapp_columns():
            query = query.or_(
                "reminder_sent.eq.false,whatsapp_reminder_sent.eq.false"
            )
        else:
            query = query.eq("reminder_sent", False)
        appointments = query.execute().data

        for appt in appointments:
            if appt.get("status") in {"Completed", "Cancelled"}:
                continue
            appt_time = parse_database_datetime(appt["appointment_time"])
            if now <= appt_time <= next_hour:
                message = (
                    f"Reminder: {appt['customer_name']}, your appointment is at "
                    f"{appt_time.strftime('%Y-%m-%d %H:%M UTC')}."
                )
                results = dispatch_message(database, appt, "reminder", message)
                updates = delivery_updates("reminder", results)
                if len(updates) > 1:
                    database.table("appointments").update(updates).eq(
                        "id", appt["id"]
                    ).execute()
    except Exception:
        logger.exception("Reminder job failed")


scheduler = BackgroundScheduler(timezone="UTC")


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler.add_job(
        check_reminders,
        "interval",
        minutes=5,
        id="appointment-reminders",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="Appointment Automation API",
    version="1.0.0",
    lifespan=lifespan,
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(
    "/api/appointments",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_appointment(
    appt: AppointmentCreate,
    ai_enabled: bool = Header(default=True, alias="X-AI-Enabled"),
):
    if not appt.phone_number.startswith("+") or not appt.phone_number[1:].isdigit():
        raise HTTPException(status_code=400, detail="Use E.164 phone format, e.g. +15551234567")

    appointment_time = normalize_datetime(appt.appointment_time)
    if appointment_time <= utc_now():
        raise HTTPException(status_code=400, detail="Appointment time must be in the future")

    summary = DEFAULT_AI_SUMMARY
    if ai_enabled:
        summary = await generate_ai_summary(
            AISummaryRequest(
                customer_name=appt.customer_name,
                appointment_time=appointment_time,
                purpose=appt.purpose,
            )
        )
    data = appt.model_dump()
    data["appointment_time"] = appointment_time.isoformat()
    data.update(
        {
            "ai_summary": summary,
            "status": "Scheduled",
            "confirmation_sent": False,
            "reminder_sent": False,
        }
    )
    if supports_whatsapp_columns():
        data.update(
            {
                "whatsapp_confirmation_sent": False,
                "whatsapp_reminder_sent": False,
            }
        )

    try:
        database = get_supabase()
        result = database.table("appointments").insert(data).execute()
        if not result.data:
            raise RuntimeError("Database returned no appointment")
        new_appt = result.data[0]
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Appointment creation failed")
        raise HTTPException(status_code=500, detail="Could not create appointment") from exc

    confirmation = (
        f"Appointment scheduled for {appt.customer_name} at "
        f"{appointment_time.strftime('%Y-%m-%d %H:%M UTC')}."
    )
    results = dispatch_message(database, new_appt, "confirmation", confirmation)
    updates = delivery_updates("confirmation", results)
    if len(updates) > 1:
        try:
            updated = (
                database.table("appointments")
                .update(updates)
                .eq("id", new_appt["id"])
                .execute()
            )
            if updated.data:
                new_appt = updated.data[0]
        except Exception:
            logger.exception("Could not persist confirmation delivery status")

    return normalize_appointment_record(new_appt)


@app.get("/api/appointments", response_model=List[AppointmentResponse])
async def get_appointments():
    try:
        records = (
            get_supabase()
            .table("appointments")
            .select("*")
            .order("appointment_time")
            .execute()
            .data
        )
        return [normalize_appointment_record(record) for record in records]
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Could not fetch appointments")
        raise HTTPException(status_code=500, detail="Could not fetch appointments") from exc


@app.get("/api/appointments/{appt_id}", response_model=AppointmentResponse)
async def get_appointment(appt_id: int):
    result = (
        get_supabase().table("appointments").select("*").eq("id", appt_id).execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return normalize_appointment_record(result.data[0])


@app.patch("/api/appointments/{appt_id}/status", response_model=AppointmentResponse)
async def update_status(
    appt_id: int,
    payload: Optional[StatusUpdate] = None,
    status_value: Optional[str] = Query(default=None, alias="status"),
):
    new_status = payload.status if payload else status_value
    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )

    result = (
        get_supabase()
        .table("appointments")
        .update({"status": new_status, "updated_at": utc_now().isoformat()})
        .eq("id", appt_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return normalize_appointment_record(result.data[0])


@app.delete("/api/appointments/{appt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(appt_id: int):
    database = get_supabase()
    existing = database.table("appointments").select("id").eq("id", appt_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Appointment not found")
    database.table("appointments").delete().eq("id", appt_id).execute()


@app.get("/api/analytics/dashboard")
async def analytics():
    all_appts = get_supabase().table("appointments").select("*").execute().data
    today = utc_now().date()
    return {
        "total": len(all_appts),
        "today": sum(
            parse_database_datetime(appt["appointment_time"]).date() == today
            for appt in all_appts
        ),
        "confirmed": sum(appt["status"] == "Confirmed" for appt in all_appts),
        "pending": sum(appt["status"] == "Scheduled" for appt in all_appts),
        "reminder_sent": sum(
            bool(appt.get("reminder_sent") or appt.get("whatsapp_reminder_sent"))
            for appt in all_appts
        ),
    }


@app.post("/api/ai/summary", response_model=AISummaryResponse)
async def ai_summary(payload: AISummaryRequest):
    summary = await generate_ai_summary(payload)
    return {
        "summary": summary,
        "configured": bool(os.getenv("GEMINI_API_KEY")),
    }


@app.get("/api/health")
async def health():
    try:
        get_supabase().table("appointments").select("id").limit(1).execute()
        database_status = "ok"
    except Exception:
        database_status = "error"

    twilio_credentials = bool(
        os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN")
    )
    mode = get_messaging_mode()
    sms_configured = bool(twilio_credentials and os.getenv("TWILIO_PHONE_NUMBER"))
    whatsapp_configured = bool(
        twilio_credentials
        and os.getenv("TWILIO_WHATSAPP_NUMBER")
        and env_enabled("TWILIO_WHATSAPP_ENABLED")
    )
    messaging_ready = (
        mode == "mock"
        or mode == "sms"
        and sms_configured
        or mode == "whatsapp"
        and whatsapp_configured
        or mode == "both"
        and sms_configured
        and whatsapp_configured
    )
    messaging_status = "configured" if messaging_ready else "missing"
    if messaging_ready and mode == "both" and not supports_whatsapp_columns():
        messaging_status = "degraded"

    return {
        "api": "ok",
        "database": database_status,
        "messaging": {
            "mode": mode,
            "status": messaging_status,
            "sms": "configured" if sms_configured else "missing",
            "whatsapp": "configured" if whatsapp_configured else "missing",
            "separate_whatsapp_tracking": supports_whatsapp_columns(),
        },
        "ai": {
            "provider": "gemini",
            "status": "configured" if os.getenv("GEMINI_API_KEY") else "missing",
            "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
