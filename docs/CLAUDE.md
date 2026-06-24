# GlobalPerks — Claude Code Quick Reference

## Auto-Build Instructions

This file is the entry point. Before writing a single line of code, Claude Code must read
ALL six documentation files in this folder. They are not optional background reading —
each one is actively referenced during specific build prompts. Skipping any will result
in incorrect implementations.

### Step 1 — Read all docs in this order (do this before anything else):

```
1. Read docs/PROJECT_OVERVIEW.md      — understand the full architecture and data model
2. Read docs/API_REFERENCE.md         — memorise all endpoints, payloads, and side effects
3. Read docs/BACKEND_ARCHITECTURE.md  — understand every module's responsibility and patterns
4. Read docs/FRONTEND_SPEC.md         — absorb all design tokens, typography, and page specs
5. Read docs/DEPLOYMENT.md            — understand the target environment and constraints
6. Read docs/PROMPTS.md               — the 8 sequential build prompts you will now execute
```

### Step 2 — Execute the build:

```
Execute each prompt in PROMPTS.md in order from PROMPT 1 through PROMPT 8.
After each prompt, run the verification steps listed before proceeding to the next.
Do not skip ahead. Do not combine prompts. Do not start coding before reading all docs.
```

---

## Why Each Doc Exists

| File | Used by prompts | What it prevents |
|---|---|---|
| `PROJECT_OVERVIEW.md` | 1, 2, 3, 4 | Building the wrong architecture or missing the dual-database pattern (Turso for bookings, SQLite for sessions) |
| `API_REFERENCE.md` | 2, 3, 7, 8 | Wrong endpoint shapes, missing email side effects, incorrect Google Calendar event structure |
| `BACKEND_ARCHITECTURE.md` | 1, 2, 3, 4, 5 | Wrong module structure, missing error handling patterns, security oversights, incorrect libsql row-to-dict pattern |
| `FRONTEND_SPEC.md` | 6, 7, 8 | Wrong fonts, wrong colors, missing components, incorrect form submission JS logic |
| `DEPLOYMENT.md` | 8 | Missing env vars, wrong build/start commands, missing one-time setup scripts |
| `PROMPTS.md` | All | The prompts themselves — contains all code to write and all verification commands |

---

## File Map

```
docs/
├── CLAUDE.md               ← YOU ARE HERE — read this first
├── PROMPTS.md              ← 8 sequential build prompts (the actual build instructions)
├── PROJECT_OVERVIEW.md     ← Architecture, tech stack, data model, build order
├── API_REFERENCE.md        ← All endpoints, request/response shapes, email/calendar specs
├── BACKEND_ARCHITECTURE.md ← Module responsibilities, code patterns, security rules
├── FRONTEND_SPEC.md        ← Design tokens, typography, component patterns, all page specs
└── DEPLOYMENT.md           ← Render deployment steps, Turso setup, Google Calendar setup
```

---

## What Gets Built

| Output | Location | Prompt |
|---|---|---|
| Django project scaffold | `backend/` | 1 |
| Turso connection + DB init | `backend/apps/core/turso.py` | 1 |
| Booking API endpoint | `backend/apps/bookings/` | 2 |
| Email service (Resend) | `backend/apps/core/email_service.py` | 3 |
| Google Calendar service | `backend/apps/core/calendar_service.py` | 3 |
| Admin create script | `backend/scripts/create_admin.py` | 3 |
| Admin auth + views | `backend/apps/admin_panel/views.py` | 4 |
| Admin dashboard UI | `backend/apps/admin_panel/templates/` | 5 |
| Homepage + Portfolio | `frontend/index.html`, `frontend/portfolio.html` | 6 |
| Services + About + Contact | `frontend/services.html`, etc. | 7 |
| Full integration + deploy config | All files | 8 |

---

## Tech Stack Summary

- **Backend:** Python · Django 5 · Django REST Framework
- **Database:** Turso (libSQL/SQLite cloud) via `libsql` Python SDK (raw SQL)
- **Email:** Resend
- **Calendar:** Google Calendar API (service account)
- **Auth:** Django sessions + bcrypt (single admin password)
- **Frontend:** Vanilla HTML/CSS/JS (no framework, no build step)
- **Fonts:** DM Serif Display + IBM Plex Mono (Google Fonts)
- **Hosting:** Render (backend as Web Service, frontend as Static Site)

---

## Environment Variables Needed

Collect these before starting:

| Variable | Where to get it |
|---|---|
| `DJANGO_SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `TURSO_DATABASE_URL` | turso.tech dashboard after creating DB |
| `TURSO_AUTH_TOKEN` | turso.tech dashboard |
| `RESEND_API_KEY` | resend.com → API Keys |
| `RESEND_FROM_EMAIL` | Your verified sending domain |
| `NOTIFICATION_EMAIL` | Photographer's email address |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Google Cloud Console → Service Account → JSON key |
| `GOOGLE_CALENDAR_ID` | Google Calendar settings → Integrate calendar |

---

## Brand Colors (for reference)

| Token | Value | Usage |
|---|---|---|
| `--gold-light` | `#D9A640` | Primary accent, CTAs, highlights |
| `--gold` | `#BF8C2C` | Hover states |
| `--gold-dim` | `#8C6520` | Subtle accents, focus states |
| `--bg-dark` | `#0A0A0A` | Page background |
| `--bg-surface` | `#141414` | Section backgrounds |
| `--bg-card` | `#1A1A1A` | Cards, admin surfaces |
| `--text-primary` | `#F5F5F0` | Main text |
| `--text-secondary` | `#A0A09A` | Supporting text |
| `--text-muted` | `#606058` | Labels, captions |

---

## Fonts

- **Display:** `DM Serif Display` — headings, hero text
- **Body:** `IBM Plex Mono` — everything else (monospace creates editorial texture)

---

## Key Decisions Made

1. **Turso via raw SQL** (not ORM) — stable `libsql` package, direct control
2. **Django sessions in SQLite** — only for admin auth, bookings never touch Django ORM
3. **Vanilla HTML frontend** — no framework, no build step, matches GR TECH pattern
4. **Threading for emails** — non-blocking API response, fire-and-forget email send
5. **Google Calendar on status change** — only fires when admin confirms booking
6. **Single admin password** — no multi-user, no OAuth, bcrypt hashed
7. **WhiteNoise** — Django serves its own static files, no separate CDN needed for admin

---

## Common Issues and Fixes

**`libsql` connection error on startup:**
→ Check `TURSO_DATABASE_URL` starts with `libsql://` not `https://`
→ Check `TURSO_AUTH_TOKEN` is not expired (create new one in Turso dashboard)

**CORS error when submitting form:**
→ Check `CORS_ALLOWED_ORIGINS` in backend env includes the exact frontend origin
→ Include both `http://` and `https://` variants during development

**Admin login always fails:**
→ Run `python scripts/create_admin.py` if admin_users table is empty
→ Check Turso tables exist: run `python scripts/init_db.py` first

**Google Calendar events not creating:**
→ Check `GOOGLE_SERVICE_ACCOUNT_JSON` is valid JSON (parse test: `echo $GOOGLE_SERVICE_ACCOUNT_JSON | python3 -m json.tool`)
→ Confirm service account email has been shared with the calendar
→ Check Render logs for specific error message (calendar failures are logged, not raised)

**Emails not sending:**
→ Verify `RESEND_API_KEY` is set correctly
→ Verify `RESEND_FROM_EMAIL` domain is verified in Resend dashboard
→ Check Django logs — email errors are caught and logged with `logger.error`

**Static files 404 in production:**
→ Confirm `python manage.py collectstatic --noinput` ran in build command
→ Check `STATIC_ROOT` is set to `BASE_DIR / 'staticfiles'`
→ Confirm WhiteNoise is in MIDDLEWARE above all other middleware except SecurityMiddleware
