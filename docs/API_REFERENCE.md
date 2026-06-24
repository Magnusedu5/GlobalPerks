# GlobalPerks API Reference

## Base URL
- **Development:** `http://localhost:8000`
- **Production:** `https://globalperks-backend.onrender.com`

---

## Public Endpoints

### POST /api/bookings/

Submit a new booking inquiry from the public website.

**Authentication:** None required

**Request body (JSON):**
```json
{
  "name": "Amara Okafor",
  "email": "amara@example.com",
  "phone": "+234 801 234 5678",
  "service": "wedding",
  "preferred_date": "2025-03-15",
  "message": "Looking for full-day wedding coverage in Lagos."
}
```

**Field validation:**
| Field | Type | Required | Rules |
|---|---|---|---|
| name | string | yes | max 100 chars |
| email | string | yes | valid email format |
| phone | string | yes | max 20 chars |
| service | string | yes | one of: `portraits`, `wedding`, `commercial`, `events`, `travel` |
| preferred_date | string | yes | ISO date format: YYYY-MM-DD |
| message | string | no | max 1000 chars |

**Success response — 201 Created:**
```json
{
  "success": true,
  "message": "Booking received"
}
```

**Validation error — 400 Bad Request:**
```json
{
  "email": ["Enter a valid email address."],
  "service": ["\"party\" is not a valid choice."]
}
```

**Server error — 500 Internal Server Error:**
```json
{
  "error": "Something went wrong. Please try again."
}
```

**Side effects on success:**
- Booking inserted into Turso with `status = "pending"`
- Auto-reply email sent to client via Resend (non-blocking thread)
- Notification email sent to `NOTIFICATION_EMAIL` via Resend (non-blocking thread)

---

## Admin Endpoints

All admin endpoints require an active session (set by `/admin-panel/login/`). Unauthenticated requests are redirected to `/admin-panel/login/`.

---

### GET /admin-panel/login/
Renders the admin login HTML page.

### POST /admin-panel/login/
Authenticates the admin.

**Form data:**
| Field | Type | Required |
|---|---|---|
| password | string | yes |
| csrfmiddlewaretoken | string | yes |

**On success:** Redirects to `/admin-panel/bookings/`
**On failure:** Re-renders login page with error message

---

### POST /admin-panel/logout/
Destroys the admin session.

**On success:** Redirects to `/admin-panel/login/`

---

### GET /admin-panel/bookings/
Renders the bookings dashboard with stats and booking list.

**Query parameters:**
| Param | Values | Description |
|---|---|---|
| status | pending \| confirmed \| declined \| completed \| archived | Filter by status |

**Renders:** `admin_panel/bookings_list.html`
**Template context:**
```python
{
  "bookings": [...],       # list of booking dicts
  "stats": {
    "total": 42,
    "pending": 7,
    "confirmed_this_month": 5,
    "completed": 28
  },
  "current_filter": "pending"  # or None
}
```

---

### GET /admin-panel/bookings/<id>/
Renders the booking detail page.

**URL params:** `id` — integer booking ID

**Query parameters:**
| Param | Value | Description |
|---|---|---|
| updated | true | Shows success banner |

**Renders:** `admin_panel/booking_detail.html`
**Template context:**
```python
{
  "booking": {
    "id": 12,
    "name": "Amara Okafor",
    "email": "amara@example.com",
    "phone": "+234 801 234 5678",
    "service": "wedding",
    "preferred_date": "2025-03-15",
    "message": "Full-day wedding coverage",
    "status": "confirmed",
    "google_calendar_event_id": "abc123xyz",
    "created_at": "2025-01-20 14:32:00"
  },
  "show_success": True
}
```

**404:** If booking ID does not exist, returns 404 response.

---

### POST /admin-panel/bookings/<id>/
Updates the booking status. Triggers Google Calendar sync when status → confirmed.

**Form data:**
| Field | Type | Required |
|---|---|---|
| status | string | yes — one of: pending \| confirmed \| declined \| completed \| archived |
| csrfmiddlewaretoken | string | yes |

**On success:** Redirects to `/admin-panel/bookings/<id>/?updated=true`

**Google Calendar trigger:**
- Fires when `new_status == "confirmed"` AND `booking.google_calendar_event_id` is None
- Calendar event creation failure is silent (logged only) — redirect still succeeds

---

## Booking Status State Machine

```
            [new inquiry]
                 ↓
            PENDING
           /       \
      CONFIRMED   DECLINED
          ↓
      COMPLETED
          ↓
      ARCHIVED
```

Valid status transitions (any → any is allowed in admin, but logical flow above):
- `pending` → `confirmed` (triggers Google Calendar sync)
- `pending` → `declined`
- `confirmed` → `completed`
- `completed` → `archived`
- Any status → `archived`

---

## Email Templates

### Client auto-reply (sent on booking creation)
- **From:** `RESEND_FROM_EMAIL`
- **To:** Client's email
- **Subject:** `We received your booking request — GlobalPerks`
- **Content:** Confirms name, service, preferred date, 24-hour response promise

### Photographer notification (sent on booking creation)
- **From:** `RESEND_FROM_EMAIL`
- **To:** `NOTIFICATION_EMAIL`
- **Subject:** `New booking request — {name} ({service})`
- **Content:** All booking fields, direct link to admin detail page

---

## Google Calendar Event Structure

Created when booking status changes to `confirmed`:

```json
{
  "summary": "Wedding — Amara Okafor",
  "description": "Client: Amara Okafor\nEmail: amara@example.com\nPhone: +234 801 234 5678\nMessage: Full-day wedding coverage",
  "start": {
    "dateTime": "2025-03-15T09:00:00",
    "timeZone": "Africa/Lagos"
  },
  "end": {
    "dateTime": "2025-03-15T11:00:00",
    "timeZone": "Africa/Lagos"
  },
  "attendees": [
    { "email": "amara@example.com" }
  ],
  "sendUpdates": "all"
}
```

The returned event `id` is stored in `bookings.google_calendar_event_id`.
