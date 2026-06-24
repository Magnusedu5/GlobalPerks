# GlobalPerks — Deployment Guide

## Pre-Deployment Checklist

Before deploying to Render, verify every item in this checklist.

### Code
- [ ] All 8 prompts have been run and verified
- [ ] `python manage.py runserver` starts with no errors
- [ ] End-to-end booking flow works locally
- [ ] Admin login works locally
- [ ] No hardcoded localhost URLs in Python files
- [ ] All TODO comments resolved or documented
- [ ] `.env.example` matches all vars used in `settings.py`

### Security
- [ ] `DEBUG=False` will be set in production env
- [ ] `DJANGO_SECRET_KEY` is a long random string (50+ chars)
- [ ] `SESSION_COOKIE_SECURE=True` (automatic when DEBUG=False)
- [ ] Admin password is strong (12+ chars, mixed)
- [ ] CORS origins locked to actual frontend domain
- [ ] No sensitive data in `requirements.txt` or committed files

---

## Step 1 — Set Up Turso Database

1. Go to [turso.tech](https://turso.tech) and sign up / log in
2. Create a new database:
   ```bash
   turso db create globalperks-db
   ```
3. Get the database URL:
   ```bash
   turso db show globalperks-db --url
   # Returns: libsql://globalperks-db-<org>.turso.io
   ```
4. Create an auth token:
   ```bash
   turso db tokens create globalperks-db
   ```
5. Save both values — you'll need them for Render env vars

---

## Step 2 — Set Up Resend

1. Go to [resend.com](https://resend.com) and sign up
2. Verify your sending domain (add DNS records)
3. Create an API key at resend.com/api-keys
4. Set `RESEND_FROM_EMAIL` to an email on your verified domain

---

## Step 3 — Set Up Google Calendar API

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project: "GlobalPerks"
3. Enable the Google Calendar API:
   - APIs & Services → Enable APIs
   - Search "Google Calendar API" → Enable
4. Create a Service Account:
   - IAM & Admin → Service Accounts → Create
   - Name: "globalperks-calendar"
   - Role: Project > Editor (or just Calendar access)
5. Create and download JSON key:
   - Click the service account → Keys → Add Key → JSON
   - Download the `.json` file
6. Share your Google Calendar with the service account:
   - Open Google Calendar
   - Settings → Your calendar → Share with specific people
   - Add the service account email (found in the JSON: `client_email`)
   - Permission: "Make changes to events"
7. Get your Calendar ID:
   - Calendar Settings → Integrate calendar → Calendar ID
   - Looks like: `abc123@group.calendar.google.com` or your Gmail for primary
8. Convert the JSON key to a single-line string for the env var:
   ```bash
   cat service-account.json | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)))"
   ```
   Copy the output — this is your `GOOGLE_SERVICE_ACCOUNT_JSON` env var value

---

## Step 4 — Deploy Backend to Render

1. Push backend code to GitHub:
   ```bash
   cd globalperks/backend
   git init
   git add .
   git commit -m "Initial GlobalPerks backend"
   git remote add origin https://github.com/YOUR_USERNAME/globalperks-backend.git
   git push -u origin main
   ```

2. Go to [render.com](https://render.com) → New → Web Service

3. Connect your GitHub repository

4. Configure the service:
   - **Name:** `globalperks-backend`
   - **Region:** Choose closest to Lagos (Frankfurt or Ohio)
   - **Branch:** `main`
   - **Build command:**
     ```
     pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
     ```
   - **Start command:**
     ```
     gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2
     ```

5. Add Environment Variables (click "Advanced" or "Environment"):

   | Key | Value |
   |---|---|
   | `DJANGO_SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
   | `DEBUG` | `False` |
   | `ALLOWED_HOSTS` | `globalperks-backend.onrender.com` (update with real URL) |
   | `CORS_ALLOWED_ORIGINS` | `https://globalperks.onrender.com` (update with frontend URL) |
   | `TURSO_DATABASE_URL` | From Step 1 |
   | `TURSO_AUTH_TOKEN` | From Step 1 |
   | `RESEND_API_KEY` | From Step 2 |
   | `RESEND_FROM_EMAIL` | `bookings@globalperks.com` |
   | `NOTIFICATION_EMAIL` | Photographer's email |
   | `GOOGLE_SERVICE_ACCOUNT_JSON` | Full JSON string from Step 3 |
   | `GOOGLE_CALENDAR_ID` | From Step 3 |

6. Click **Create Web Service** → wait for build (3–5 minutes)

7. Once deployed, open the Render shell (Connect → Shell) and run:
   ```bash
   python scripts/init_db.py
   python scripts/create_admin.py
   ```

8. Note the backend URL: `https://globalperks-backend.onrender.com`

9. Smoke test:
   ```bash
   curl https://globalperks-backend.onrender.com/health/
   # → {"status": "ok", "service": "globalperks-backend"}
   ```

---

## Step 5 — Deploy Frontend to Render

1. Before pushing: update the backend URL in `contact.html`:
   ```javascript
   // Find this line and update:
   : 'https://your-backend.onrender.com';
   // Replace with:
   : 'https://globalperks-backend.onrender.com';
   ```

2. Push frontend to GitHub:
   ```bash
   cd globalperks/frontend
   git init
   git add .
   git commit -m "Initial GlobalPerks frontend"
   git remote add origin https://github.com/YOUR_USERNAME/globalperks-frontend.git
   git push -u origin main
   ```

3. Go to Render → New → Static Site

4. Configure:
   - **Name:** `globalperks`
   - **Branch:** `main`
   - **Publish directory:** `.` (or `frontend` if repo root is `globalperks/`)
   - No build command

5. Deploy → note the URL: `https://globalperks.onrender.com`

6. Go back to backend service → Environment → Update `CORS_ALLOWED_ORIGINS`:
   ```
   https://globalperks.onrender.com
   ```
   Redeploy backend (or it will auto-redeploy on env var change).

---

## Step 6 — Post-Deployment Verification

```bash
# 1. Health check
curl https://globalperks-backend.onrender.com/health/

# 2. Submit a test booking
curl -X POST https://globalperks-backend.onrender.com/api/bookings/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Deploy Test","email":"test@test.com","phone":"+234 800 000 0000","service":"portraits","preferred_date":"2025-06-15","message":"Deployment test"}'
# → {"success": true, "message": "Booking received"}

# 3. Check email received at NOTIFICATION_EMAIL

# 4. Visit admin panel
# https://globalperks-backend.onrender.com/admin-panel/login/
# Log in → see the test booking

# 5. Change status to Confirmed → check Google Calendar
```

---

## Custom Domain (Optional)

To use `globalperks.com` instead of `globalperks.onrender.com`:

1. Buy domain from Namecheap / Cloudflare Registrar
2. Render → Static Site → Custom Domains → Add domain
3. Add the DNS records Render provides (CNAME or A record)
4. Update backend `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` with new domain
5. Update `contact.html` JS with new backend URL (if also adding custom domain to backend)

---

## Monitoring & Maintenance

**Logs:** Render → Service → Logs tab — all Python `logger` calls appear here

**Turso usage:** turso.tech dashboard shows query count, storage, bandwidth

**Resend usage:** resend.com dashboard shows email delivery status

**When to scale Gunicorn workers:**
- Current: `--workers 2` (fine for 0–100 bookings/month)
- Upgrade to 4 workers if response times degrade under load

**Database backup:**
Turso handles backups automatically on paid plans. For free tier:
```bash
# Export via Turso CLI
turso db shell globalperks-db ".dump" > backup-$(date +%Y%m%d).sql
```
