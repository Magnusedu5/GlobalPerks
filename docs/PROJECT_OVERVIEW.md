# GlobalPerks Photography — Project Overview

## What We're Building

A full-stack photography website for **GlobalPerks**, a professional photographer brand. The site has two distinct sides:

1. **Public website** — a stunning, conversion-focused portfolio site where potential clients browse work, learn about services, and submit booking requests
2. **Admin dashboard** — a password-protected internal tool where the photographer manages all incoming bookings, updates statuses, and views calendar syncs

---

## Architecture at a Glance

```
globalperks/
├── frontend/          ← Static HTML/CSS/JS (no framework)
│   ├── index.html
│   ├── portfolio.html
│   ├── services.html
│   ├── about.html
│   └── contact.html
│
└── backend/           ← Django REST Framework (Python)
    ├── config/        ← Django settings, urls, wsgi
    ├── apps/
    │   ├── bookings/  ← Public API: POST /api/bookings/
    │   ├── admin_panel/ ← Protected admin dashboard UI
    │   └── core/      ← Turso client, email, calendar services
    └── scripts/       ← DB init + admin seed scripts
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | Vanilla HTML/CSS/JS | No build step, easy to deploy, matches GR TECH pattern |
| Backend | Django 5.x + DRF | Robust, batteries-included, Python ecosystem |
| Database | Turso (libSQL/SQLite cloud) | Free tier, edge-hosted, SQLite-compatible |
| DB access | `libsql` Python SDK (raw SQL) | Stable, no ORM complexity for booking queries |
| Email | Resend | Already in use at GR TECH |
| Calendar | Google Calendar API | Confirmed bookings auto-sync to photographer's calendar |
| Auth | Django sessions + bcrypt | Single admin password, no OAuth needed |
| Hosting | Render | Consistent with GR TECH backend |
| Static files | WhiteNoise | Serves Django static files in production |

---

## Data Architecture

### Turso (booking data — raw SQL via libsql)
```sql
CREATE TABLE bookings (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    name                    TEXT NOT NULL,
    email                   TEXT NOT NULL,
    phone                   TEXT NOT NULL,
    service                 TEXT NOT NULL,  -- portraits|wedding|commercial|events|travel
    preferred_date          TEXT NOT NULL,  -- YYYY-MM-DD
    message                 TEXT,
    status                  TEXT NOT NULL DEFAULT 'pending',  -- pending|confirmed|declined|completed|archived
    google_calendar_event_id TEXT,
    created_at              TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE admin_users (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    password_hash  TEXT NOT NULL,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### Django SQLite (sessions only — local db.sqlite3)
Django's built-in session framework uses this. The bookings table is **never** touched by Django ORM.

---

## Booking Flow

```
Client fills form (frontend)
        ↓
POST /api/bookings/ (DRF)
        ↓
Validate with BookingSerializer
        ↓
Insert into Turso via libsql
        ↓
Fire two emails via Resend (threaded — non-blocking):
  • Auto-reply to client
  • Notification to photographer
        ↓
Return { success: true } → Show confirmation on frontend
```

## Admin Flow

```
Photographer visits /admin-panel/login/
        ↓
Enters password → bcrypt compare → session set
        ↓
/admin-panel/bookings/ → Full booking list + stats
        ↓
Click booking → /admin-panel/bookings/<id>/
        ↓
Change status → POST form
        ↓
If status = "confirmed" + no calendar event:
    → Google Calendar API → create event → save event ID
        ↓
Redirect back with success banner
```

---

## Environment Variables Required

```
# Django
DJANGO_SECRET_KEY=
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://globalperks.com

# Turso
TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=

# Email
RESEND_API_KEY=
RESEND_FROM_EMAIL=bookings@globalperks.com
NOTIFICATION_EMAIL=photographer@globalperks.com

# Google Calendar
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
GOOGLE_CALENDAR_ID=

# Admin
SESSION_SECRET_KEY=  (use DJANGO_SECRET_KEY for sessions)
```

---

## Deployment (Render)

**Build command:**
```
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
```

**Start command:**
```
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2
```

**One-time setup (run via Render shell):**
```bash
python scripts/init_db.py      # Creates Turso tables
python scripts/create_admin.py # Sets admin password
```

---

## Brand Design Tokens

```css
/* Colors */
--gold-light:  #D9A640;
--gold:        #BF8C2C;
--gold-dim:    #8C6520;
--bg-dark:     #0A0A0A;
--bg-surface:  #141414;
--bg-card:     #1A1A1A;
--border:      #2A2A2A;
--text-primary: #F5F5F0;
--text-secondary: #A0A09A;
--text-muted:  #606058;

/* Typography */
--font-display: 'DM Serif Display', Georgia, serif;
--font-body:    'IBM Plex Mono', 'Courier New', monospace;

/* Spacing scale */
--space-xs: 0.5rem;
--space-sm: 1rem;
--space-md: 2rem;
--space-lg: 4rem;
--space-xl: 8rem;
```

---

## Build Order

The project is built in **8 sequential phases**. Each phase produces working, testable code before the next begins.

| Phase | What gets built | Testable after? |
|---|---|---|
| 1 | Django project scaffold + Turso connection | `python manage.py runserver` works |
| 2 | Bookings app — models, serializer, API endpoint | `POST /api/bookings/` returns 201 |
| 3 | Email service (Resend) + Google Calendar service | Emails send on booking |
| 4 | Admin panel — auth, views, URL routing | Login page renders |
| 5 | Admin HTML templates — full dashboard UI | Full admin works end-to-end |
| 6 | Frontend — Homepage + Portfolio | Opens in browser |
| 7 | Frontend — Services + About + Contact pages | All pages link correctly |
| 8 | Frontend booking form wired to backend | Full end-to-end booking flow works |
