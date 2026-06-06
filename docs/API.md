# API Summary

Full interactive documentation is available at `/docs`.

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/appointments` | Create an appointment and attempt configured confirmation delivery |
| `GET` | `/api/appointments` | List appointments ordered by time |
| `GET` | `/api/appointments/{id}` | Get one appointment |
| `PATCH` | `/api/appointments/{id}/status` | Update appointment status |
| `DELETE` | `/api/appointments/{id}` | Delete an appointment |
| `GET` | `/api/analytics/dashboard` | Return dashboard counts |
| `POST` | `/api/ai/summary` | Generate a summary or fallback text |
| `GET` | `/api/health` | Report API, database, messaging, and AI status |

## Create Appointment

```json
{
  "customer_name": "Taylor Smith",
  "phone_number": "+15551234567",
  "appointment_time": "2026-06-07T10:30:00Z",
  "purpose": "Discuss plan upgrade options"
}
```

The API stores the appointment before attempting messaging. A Twilio failure
leaves the relevant SMS or WhatsApp delivery flag as `false` but does not fail
the booking. Mock mode marks the generic delivery flag and writes an audit log.

The optional `X-AI-Enabled: false` header skips summary generation for that
request.

## Update Status

```json
{
  "status": "Confirmed"
}
```

Valid values are `Scheduled`, `Confirmed`, `Reminder Sent`, `Completed`, and
`Cancelled`. The endpoint also accepts the legacy `?status=Confirmed` query
parameter.

## Messaging Modes

- `mock`: no external request; log the simulated message.
- `sms`: send only through the Twilio SMS sender.
- `whatsapp`: send only through the Twilio WhatsApp Sandbox or approved sender.
- `both`: attempt both and retry only an unsuccessful channel.

## Analytics Response

```json
{
  "total": 18,
  "today": 4,
  "confirmed": 7,
  "pending": 5,
  "reminder_sent": 9
}
```

## Error Behavior

Validation errors return `400`, missing records return `404`, missing database
configuration returns `503`, and unexpected database failures return `500`.
