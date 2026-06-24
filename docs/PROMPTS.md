# GlobalPerks — Claude Code Build Prompts

**Read this file first.** This document contains all build prompts for the GlobalPerks photography website, designed to be executed sequentially in Claude Code. Each prompt is self-contained, testable, and builds on the previous one.

Before starting, read the companion documents in this folder:
- `PROJECT_OVERVIEW.md` — Full architecture, stack decisions, data model
- `API_REFERENCE.md` — All endpoints, request/response shapes, email and calendar specs
- `BACKEND_ARCHITECTURE.md` — Module responsibilities, code patterns, security checklist
- `FRONTEND_SPEC.md` — Design tokens, typography, component patterns, page specifications

---

## How to use this file

1. Open Claude Code in your terminal from the project root
2. Paste **one prompt at a time** — do not combine prompts
3. Wait for Claude Code to finish and confirm before moving to the next
4. After each prompt, run the listed **verification steps**
5. Only proceed when verification passes

---

## Project root structure expected before starting

```
globalperks/
├── backend/     ← Django project lives here
├── frontend/    ← Static HTML site lives here
└── docs/        ← This folder (PROJECT_OVERVIEW.md etc.)
```

If these folders don't exist, create them before starting:
```bash
mkdir -p globalperks/backend globalperks/frontend globalperks/docs
```

---

---

# PROMPT 1 — Django Project Scaffold + Turso Connection

```
Read the file docs/PROJECT_OVERVIEW.md and docs/BACKEND_ARCHITECTURE.md before writing any code.

Set up the complete Django REST Framework project scaffold for GlobalPerks inside the `backend/` directory. Do the following exactly:

## 1. Create requirements.txt
```
django>=5.0,<6.0
djangorestframework>=3.15
libsql>=0.4.0
resend>=2.0.0
google-api-python-client>=2.100.0
google-auth>=2.23.0
google-auth-httplib2>=0.1.0
bcrypt>=4.0.0
python-dotenv>=1.0.0
gunicorn>=21.0.0
django-cors-headers>=4.3.0
whitenoise>=6.6.0
```

## 2. Create the Django project
Run: django-admin startproject config .
(run this from inside the backend/ directory)

## 3. Create the app directories
Run from backend/:
- python manage.py startapp bookings apps/bookings
- python manage.py startapp admin_panel apps/admin_panel  
- python manage.py startapp core apps/core

## 4. Create config/settings.py
Replace the default settings.py entirely with a production-ready settings file that:
- Loads env vars using python-dotenv (call load_dotenv() at the top)
- SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
- DEBUG = os.environ.get('DEBUG', 'False') == 'True'
- ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
- INSTALLED_APPS includes: django.contrib.auth, django.contrib.contenttypes, django.contrib.sessions, django.contrib.messages, django.contrib.staticfiles, rest_framework, corsheaders, apps.bookings, apps.admin_panel, apps.core
- MIDDLEWARE includes CorsMiddleware (first), SecurityMiddleware (second), WhiteNoiseMiddleware (third), then all Django defaults including SessionMiddleware and AuthenticationMiddleware
- DATABASES = { 'default': { 'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3' } }
- SESSION_COOKIE_HTTPONLY = True
- SESSION_COOKIE_SECURE = not DEBUG
- SESSION_COOKIE_SAMESITE = 'Strict'
- SESSION_COOKIE_AGE = 86400
- CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
- STATIC_URL = '/static/'
- STATIC_ROOT = BASE_DIR / 'staticfiles'
- STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
- TEMPLATES configured to find templates in each app's templates/ folder using APP_DIRS = True
- REST_FRAMEWORK = { 'DEFAULT_AUTHENTICATION_CLASSES': [], 'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'] }

## 5. Create config/urls.py
```python
from django.urls import path, include

urlpatterns = [
    path('api/', include('apps.bookings.urls')),
    path('admin-panel/', include('apps.admin_panel.urls')),
]
```
Do NOT include Django's default admin URLs.

## 6. Create apps/core/turso.py
```python
import libsql
import os
import logging

logger = logging.getLogger(__name__)
_conn = None

def get_connection():
    global _conn
    if _conn is None:
        _conn = libsql.connect(
            database=os.environ['TURSO_DATABASE_URL'],
            auth_token=os.environ['TURSO_AUTH_TOKEN'],
        )
    return _conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            service TEXT NOT NULL,
            preferred_date TEXT NOT NULL,
            message TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            google_calendar_event_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    logger.info("Turso tables initialised")
```

## 7. Create scripts/init_db.py
```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from apps.core.turso import init_db
init_db()
print("Database tables created successfully.")
```

## 8. Create .env.example
```
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:5500

TURSO_DATABASE_URL=libsql://your-db-name.turso.io
TURSO_AUTH_TOKEN=

RESEND_API_KEY=
RESEND_FROM_EMAIL=bookings@globalperks.com
NOTIFICATION_EMAIL=

GOOGLE_SERVICE_ACCOUNT_JSON=
GOOGLE_CALENDAR_ID=
```

## 9. Create Procfile
```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2
```

## 10. Create stub URL files so the project starts without errors
- apps/bookings/urls.py: empty urlpatterns = []
- apps/admin_panel/urls.py: empty urlpatterns = []

## 11. Make sure all apps/__init__.py files exist (empty files)

After all files are created:
- Run: pip install -r requirements.txt
- Run: python manage.py migrate
- Confirm: python manage.py runserver starts without errors
```

**Verification steps after Prompt 1:**
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
# → Should see "Starting development server at http://127.0.0.1:8000/" with no errors
# → Visit http://127.0.0.1:8000/api/ — should return 404 (no routes yet, that's fine)
```

---

---

# PROMPT 2 — Bookings App: Serializer, Service, API Endpoint

```
Read docs/API_REFERENCE.md and docs/BACKEND_ARCHITECTURE.md before writing any code.

Build the complete bookings app for GlobalPerks. All files go inside backend/apps/bookings/.

## 1. apps/bookings/serializers.py

Create BookingSerializer as a DRF Serializer (NOT ModelSerializer — there is no Django model):

```python
from rest_framework import serializers

VALID_SERVICES = ['portraits', 'wedding', 'commercial', 'events', 'travel']

class BookingSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    service = serializers.ChoiceField(choices=VALID_SERVICES)
    preferred_date = serializers.DateField()
    message = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        default=''
    )
```

## 2. apps/bookings/services.py

Create TursoBookingService class. Import get_connection from apps.core.turso. All methods use raw SQL with ? placeholders (never f-strings for values). Every method is wrapped in its own error handling.

Methods to implement:

create_booking(self, data: dict) -> dict
- INSERT INTO bookings (name, email, phone, service, preferred_date, message) VALUES (?, ?, ?, ?, ?, ?)
- conn.commit()
- Fetch the inserted row by lastrowid and return as dict

get_all_bookings(self, status_filter: str = None) -> list[dict]
- If status_filter: SELECT * FROM bookings WHERE status = ? ORDER BY created_at DESC
- Else: SELECT * FROM bookings ORDER BY created_at DESC
- Return list of dicts

get_booking_by_id(self, booking_id: int) -> dict | None
- SELECT * FROM bookings WHERE id = ?
- Return dict or None if not found

update_booking_status(self, booking_id: int, new_status: str) -> dict
- UPDATE bookings SET status = ? WHERE id = ?
- conn.commit()
- Return updated booking dict

update_calendar_event_id(self, booking_id: int, event_id: str) -> None
- UPDATE bookings SET google_calendar_event_id = ? WHERE id = ?
- conn.commit()

get_stats(self) -> dict
- Run 4 queries and return:
  {
    'total': int,
    'pending': int,
    'confirmed_this_month': int,
    'completed': int
  }
- confirmed_this_month query: SELECT COUNT(*) FROM bookings WHERE status = 'confirmed' AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')

_row_to_dict(self, cursor, row) -> dict
- Uses cursor.description to get column names
- Returns dict(zip(column_names, row))
- Note: libsql cursor description is a list of sequences where index 0 is the column name

## 3. apps/bookings/views.py

Create BookingCreateView(APIView). Import: APIView from rest_framework.views, Response from rest_framework.response, BookingSerializer, TursoBookingService, and the two email functions from apps.core.email_service (import them but make email_service.py a stub for now if it doesn't exist yet — add a TODO comment). Use threading.Thread for email sending.

```python
import threading
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import BookingSerializer
from .services import TursoBookingService

logger = logging.getLogger(__name__)

class BookingCreateView(APIView):
    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        try:
            data = dict(serializer.validated_data)
            data['preferred_date'] = str(data['preferred_date'])
            service = TursoBookingService()
            booking = service.create_booking(data)
            # Send emails in background (import lazily to avoid circular imports)
            try:
                from apps.core.email_service import send_booking_confirmation, send_booking_notification
                threading.Thread(target=send_booking_confirmation, args=(booking,), daemon=True).start()
                threading.Thread(target=send_booking_notification, args=(booking,), daemon=True).start()
            except ImportError:
                pass
            return Response({'success': True, 'message': 'Booking received'}, status=201)
        except Exception as e:
            logger.error(f"Booking creation failed: {e}", exc_info=True)
            return Response({'error': 'Something went wrong. Please try again.'}, status=500)
```

## 4. apps/bookings/urls.py

```python
from django.urls import path
from .views import BookingCreateView

urlpatterns = [
    path('bookings/', BookingCreateView.as_view(), name='booking-create'),
]
```

## 5. After writing all files, test manually:
- Ensure python manage.py runserver still starts without errors
```

**Verification steps after Prompt 2:**
```bash
python manage.py runserver
# In a new terminal:
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Client","email":"test@test.com","phone":"+234 800 000 0000","service":"portraits","preferred_date":"2025-06-15","message":"Test booking"}'
# → Should return: {"success": true, "message": "Booking received"}

# Test validation:
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -d '{"name":"","email":"notanemail","service":"invalid"}'
# → Should return 400 with field errors
```

---

---

# PROMPT 3 — Email Service (Resend) + Google Calendar Service

```
Read docs/API_REFERENCE.md section "Email Templates" and "Google Calendar Event Structure" before writing any code.

Build the two service modules in backend/apps/core/.

## 1. apps/core/email_service.py

```python
import os
import logging
import resend

logger = logging.getLogger(__name__)
resend.api_key = os.environ.get('RESEND_API_KEY', '')

def _get_from_email():
    return os.environ.get('RESEND_FROM_EMAIL', 'bookings@globalperks.com')

def send_booking_confirmation(booking_data: dict) -> None:
    """Auto-reply to client. Never raises."""
    try:
        name = booking_data.get('name', '')
        email = booking_data.get('email', '')
        service = booking_data.get('service', '').title()
        date = booking_data.get('preferred_date', '')

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background:#0A0A0A;font-family:'Courier New',monospace;">
          <div style="max-width:600px;margin:0 auto;padding:40px 20px;">
            <div style="border-bottom:1px solid #2A2A2A;padding-bottom:24px;margin-bottom:32px;">
              <h1 style="color:#D9A640;font-family:Georgia,serif;font-size:28px;margin:0;font-weight:normal;">
                GlobalPerks
              </h1>
              <p style="color:#606058;font-size:11px;letter-spacing:0.1em;text-transform:uppercase;margin:4px 0 0;">
                Premium Photography
              </p>
            </div>
            <p style="color:#A0A09A;font-size:14px;line-height:1.7;margin:0 0 16px;">
              Hi {name},
            </p>
            <p style="color:#F5F5F0;font-size:16px;line-height:1.7;margin:0 0 24px;">
              Thank you for reaching out. Your booking request has been received and we're excited to hear from you.
            </p>
            <div style="background:#1A1A1A;border:1px solid #2A2A2A;border-left:3px solid #D9A640;padding:20px 24px;margin:0 0 32px;">
              <p style="color:#606058;font-size:11px;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 12px;">
                Your Request
              </p>
              <p style="color:#F5F5F0;font-size:14px;margin:0 0 8px;">
                <span style="color:#A0A09A;">Service:</span> {service}
              </p>
              <p style="color:#F5F5F0;font-size:14px;margin:0;">
                <span style="color:#A0A09A;">Preferred date:</span> {date}
              </p>
            </div>
            <p style="color:#A0A09A;font-size:14px;line-height:1.7;margin:0 0 32px;">
              We'll review your request and get back to you within <strong style="color:#F5F5F0;">24 hours</strong> to confirm availability and discuss the details.
            </p>
            <p style="color:#606058;font-size:13px;line-height:1.7;margin:0;border-top:1px solid #2A2A2A;padding-top:24px;">
              GlobalPerks Photography<br>
              Lagos, Nigeria · Shooting Worldwide
            </p>
          </div>
        </body>
        </html>
        """

        resend.Emails.send({
            "from": _get_from_email(),
            "to": [email],
            "subject": "We received your booking request — GlobalPerks",
            "html": html_body,
        })
        logger.info(f"Confirmation email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {e}")


def send_booking_notification(booking_data: dict) -> None:
    """Alert to photographer. Never raises."""
    try:
        notification_email = os.environ.get('NOTIFICATION_EMAIL', '')
        if not notification_email:
            logger.warning("NOTIFICATION_EMAIL not set — skipping notification")
            return

        name = booking_data.get('name', '')
        email = booking_data.get('email', '')
        phone = booking_data.get('phone', '')
        service = booking_data.get('service', '').title()
        date = booking_data.get('preferred_date', '')
        message = booking_data.get('message', 'No message provided')
        booking_id = booking_data.get('id', '')

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background:#0A0A0A;font-family:'Courier New',monospace;">
          <div style="max-width:600px;margin:0 auto;padding:40px 20px;">
            <div style="background:#1A1A1A;border:1px solid #2A2A2A;border-top:3px solid #D9A640;padding:24px;">
              <p style="color:#606058;font-size:11px;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 16px;">
                New Booking Request
              </p>
              <table style="width:100%;border-collapse:collapse;">
                <tr><td style="color:#A0A09A;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;width:40%;">Name</td><td style="color:#F5F5F0;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">{name}</td></tr>
                <tr><td style="color:#A0A09A;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">Email</td><td style="color:#F5F5F0;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;"><a href="mailto:{email}" style="color:#D9A640;">{email}</a></td></tr>
                <tr><td style="color:#A0A09A;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">Phone</td><td style="color:#F5F5F0;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">{phone}</td></tr>
                <tr><td style="color:#A0A09A;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">Service</td><td style="color:#F5F5F0;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">{service}</td></tr>
                <tr><td style="color:#A0A09A;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">Preferred date</td><td style="color:#F5F5F0;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">{date}</td></tr>
                <tr><td style="color:#A0A09A;font-size:13px;padding:8px 0;" valign="top">Message</td><td style="color:#F5F5F0;font-size:13px;padding:8px 0;">{message}</td></tr>
              </table>
              <div style="margin-top:24px;">
                <a href="http://localhost:8000/admin-panel/bookings/{booking_id}/"
                   style="background:#D9A640;color:#0A0A0A;padding:10px 20px;text-decoration:none;font-size:13px;font-weight:500;display:inline-block;">
                  View in Admin →
                </a>
              </div>
            </div>
          </div>
        </body>
        </html>
        """

        resend.Emails.send({
            "from": _get_from_email(),
            "to": [notification_email],
            "subject": f"New booking request — {name} ({service})",
            "html": html_body,
        })
        logger.info(f"Notification email sent for booking {booking_id}")
    except Exception as e:
        logger.error(f"Failed to send notification email: {e}")
```

## 2. apps/core/calendar_service.py

```python
import os
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

def create_calendar_event(booking: dict) -> str | None:
    """
    Creates a Google Calendar event for a confirmed booking.
    Returns the event ID on success, None on any failure. Never raises.
    """
    try:
        service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', '')
        calendar_id = os.environ.get('GOOGLE_CALENDAR_ID', '')
        
        if not service_account_json or not calendar_id:
            logger.warning("Google Calendar env vars not configured — skipping")
            return None
        
        service_account_info = json.loads(service_account_json)
        
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        
        service = build('calendar', 'v3', credentials=credentials)
        
        name = booking.get('name', '')
        service_type = booking.get('service', '').title()
        date = booking.get('preferred_date', '')
        
        event = {
            'summary': f"{service_type} — {name}",
            'description': (
                f"Client: {name}\n"
                f"Email: {booking.get('email', '')}\n"
                f"Phone: {booking.get('phone', '')}\n"
                f"Message: {booking.get('message', '')}"
            ),
            'start': {
                'dateTime': f"{date}T09:00:00",
                'timeZone': 'Africa/Lagos',
            },
            'end': {
                'dateTime': f"{date}T11:00:00",
                'timeZone': 'Africa/Lagos',
            },
            'attendees': [
                {'email': booking.get('email', '')}
            ],
            'sendUpdates': 'all',
        }
        
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event,
            sendUpdates='all'
        ).execute()
        
        event_id = created_event.get('id')
        logger.info(f"Calendar event created: {event_id} for booking {booking.get('id')}")
        return event_id
        
    except Exception as e:
        logger.error(f"Google Calendar event creation failed: {e}", exc_info=True)
        return None
```

## 3. scripts/create_admin.py

Create this standalone script:
```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
import bcrypt
import libsql

database_url = os.environ['TURSO_DATABASE_URL']
auth_token = os.environ['TURSO_AUTH_TOKEN']
conn = libsql.connect(database=database_url, auth_token=auth_token)

# Check if admin already exists
result = conn.execute("SELECT COUNT(*) FROM admin_users").fetchone()
if result[0] > 0:
    print("Admin user already exists.")
    print("To reset: run DELETE FROM admin_users in your Turso dashboard, then re-run this script.")
    sys.exit(1)

password = input("Enter admin password: ").strip()
if len(password) < 8:
    print("Password must be at least 8 characters.")
    sys.exit(1)

password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
conn.execute("INSERT INTO admin_users (password_hash) VALUES (?)", (password_hash,))
conn.commit()
print("Admin user created successfully.")
print("You can now log in at /admin-panel/login/")
```

After writing all files, confirm python manage.py runserver still starts cleanly.
```

**Verification steps after Prompt 3:**
```bash
# Post a booking again — this time emails should attempt to send
# (they'll fail gracefully if RESEND_API_KEY not set yet — check terminal logs)
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","phone":"+234 800 000 0000","service":"wedding","preferred_date":"2025-06-15"}'
# → 201 response, no 500 error
# → Terminal shows INFO log about email (warning if key not set, not an error)
```

---

---

# PROMPT 4 — Admin Panel: Auth, Views, URL Routing

```
Read docs/BACKEND_ARCHITECTURE.md sections "apps/admin_panel/decorators.py" and "apps/admin_panel/views.py" before writing any code.

Build the admin panel backend logic for GlobalPerks. Templates will be built in the next prompt — for now, create stub templates so the views don't error.

## 1. apps/admin_panel/decorators.py

```python
from functools import wraps
from django.shortcuts import redirect

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_admin'):
            return redirect('/admin-panel/login/')
        return view_func(request, *args, **kwargs)
    return wrapper
```

## 2. apps/admin_panel/views.py

Implement all five views. Import TursoBookingService from apps.bookings.services. Import create_calendar_event from apps.core.calendar_service. Use bcrypt for password comparison.

login_view(request):
- GET: render 'admin_panel/login.html' with empty context
- POST: 
  - get password from request.POST.get('password', '')
  - connect to Turso via get_connection(), execute: SELECT password_hash FROM admin_users LIMIT 1
  - if no rows: render login with {'error': 'No admin account configured'}
  - compare: bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
  - on success: request.session['is_admin'] = True, redirect to /admin-panel/bookings/
  - on failure: render login with {'error': 'Invalid password'}
  - wrap entire POST block in try/except — on exception render login with generic error

logout_view(request):
- POST only: request.session.flush(), redirect to /admin-panel/login/
- GET: redirect to /admin-panel/login/ (safety)

@admin_required
bookings_list_view(request):
- GET:
  - status_filter = request.GET.get('status', None)
  - Validate filter: if status_filter not in valid list, set to None
  - service = TursoBookingService()
  - bookings = service.get_all_bookings(status_filter)
  - stats = service.get_stats()
  - render 'admin_panel/bookings_list.html' with:
    {'bookings': bookings, 'stats': stats, 'current_filter': status_filter}

@admin_required
booking_detail_view(request, booking_id):
- GET:
  - booking = TursoBookingService().get_booking_by_id(booking_id)
  - if not booking: return HttpResponse status 404
  - show_success = request.GET.get('updated') == 'true'
  - render 'admin_panel/booking_detail.html' with:
    {'booking': booking, 'show_success': show_success}

- POST:
  - new_status = request.POST.get('status', '')
  - valid_statuses = ['pending', 'confirmed', 'declined', 'completed', 'archived']
  - if new_status not in valid_statuses:
      redirect back with error (add ?error=invalid_status)
  - service = TursoBookingService()
  - updated_booking = service.update_booking_status(booking_id, new_status)
  - if new_status == 'confirmed' and not updated_booking.get('google_calendar_event_id'):
      event_id = create_calendar_event(updated_booking)
      if event_id:
          service.update_calendar_event_id(booking_id, event_id)
  - redirect to f'/admin-panel/bookings/{booking_id}/?updated=true'

Wrap all view bodies in try/except. Log errors. Return appropriate HTTP responses on failure.

## 3. apps/admin_panel/urls.py

```python
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='admin-login'),
    path('logout/', views.logout_view, name='admin-logout'),
    path('bookings/', views.bookings_list_view, name='admin-bookings-list'),
    path('bookings/<int:booking_id>/', views.booking_detail_view, name='admin-booking-detail'),
]
```

## 4. Create stub templates (so views don't error — full templates in next prompt)

Create these files with minimal valid HTML:
- apps/admin_panel/templates/admin_panel/login.html
- apps/admin_panel/templates/admin_panel/bookings_list.html  
- apps/admin_panel/templates/admin_panel/booking_detail.html

Each stub:
```html
<!DOCTYPE html><html><body><p>{{ page_name }} — stub template</p></body></html>
```

After writing all files, confirm python manage.py runserver still starts cleanly.
```

**Verification steps after Prompt 4:**
```bash
python manage.py runserver
# Visit http://localhost:8000/admin-panel/login/ — should render the stub template (no 500 errors)
# Visit http://localhost:8000/admin-panel/bookings/ — should redirect to login (session not set)
# Visit http://localhost:8000/admin-panel/bookings/1/ — should redirect to login
```

---

---

# PROMPT 5 — Admin HTML Templates (Full Dashboard UI)

```
Read docs/FRONTEND_SPEC.md section "Admin Templates" and docs/BACKEND_ARCHITECTURE.md section "Admin Template Hierarchy" before writing any code.

Build the complete admin panel HTML templates. Replace the stub files created in Prompt 4.

All templates use inline <style> blocks only. No external CSS files. No CSS frameworks. Fonts from Google Fonts CDN only.

Design tokens to use throughout:
--bg: #0f0f0f
--surface: #1a1a1a
--surface-raised: #222222
--border: #2a2a2a
--text: #f5f5f0
--muted: #888882
--gold: #D9A640
--gold-dim: #8C6520
--red: #E24B4A
--green: #5DCAA5
--amber: #EF9F27
--blue: #85B7EB
font-family: 'IBM Plex Mono', 'Courier New', monospace

## 1. apps/admin_panel/templates/admin_panel/base.html

A Django template base that all dashboard pages extend. Includes:

<head>:
- Google Fonts: IBM Plex Mono (weights 300, 400, 500)
- {% block title %}GlobalPerks Admin{% endblock %}
- Inline <style> with CSS reset, design tokens as CSS custom properties, base styles:
  - body: background var(--bg), color var(--text), font IBM Plex Mono, margin 0
  - * box-sizing border-box
  - a: color var(--gold), text-decoration none
  - .nav: fixed top, full width, height 56px, background var(--surface), border-bottom 1px solid var(--border), display flex, align-items center, padding 0 24px, justify-content space-between, z-index 100
  - .nav-brand: color var(--gold), font-size 16px, font-weight 500, letter-spacing 0.05em
  - .nav-actions: display flex, gap 16px, align-items center
  - .btn-signout: form button, background none, border 1px solid var(--border), color var(--muted), font-family inherit, font-size 12px, padding 6px 14px, cursor pointer, letter-spacing 0.05em
  - .btn-signout:hover: border-color var(--gold-dim), color var(--gold)
  - .main: margin-top 56px, padding 32px 24px, max-width 1200px, margin-left auto, margin-right auto
  - .badge styles for all 5 statuses (see FRONTEND_SPEC.md badge section)
  - .card: background var(--surface), border 1px solid var(--border), border-radius 4px, padding 24px

<body>:
- Fixed nav bar with "GlobalPerks Admin" left + sign-out form button right
- Sign-out form: POST to /admin-panel/logout/ with CSRF token, button text "Sign out"
- <main class="main"> with {% block content %}{% endblock %}

## 2. apps/admin_panel/templates/admin_panel/login.html

Standalone page (does NOT extend base — it has its own full HTML structure).

Full-screen centered layout (flexbox, min-height 100vh, background #0f0f0f).

Center card (max-width 400px, background #1a1a1a, border 1px solid #2a2a2a, padding 40px):
- Top: "GlobalPerks" in serif-style (use Georgia since no display font in admin), color #D9A640, font-size 24px
- Subtitle: "ADMIN PANEL" — monospace, 11px, letter-spaced, color #606058, margin-top 4px
- Gold rule: hr with border-top 1px solid #2a2a2a, margin 24px 0
- If {{ error }}: error box (background rgba(226,75,74,0.1), border 1px solid rgba(226,75,74,0.3), color #F09595, padding 12px, font-size 13px, margin-bottom 20px)
- Form with POST method and {% csrf_token %}:
  - Label "Password" (11px, uppercase, letter-spaced, color #888)
  - Input type=password, name=password (full width, background #0f0f0f, border 1px solid #2a2a2a, color #f5f5f0, padding 12px, font-family inherit, font-size 14px)
  - Input:focus border-color #8C6520
  - Submit button "Sign in" (full width, background #D9A640, color #0f0f0f, border none, padding 12px, font-family inherit, font-size 14px, font-weight 500, cursor pointer, margin-top 16px)
  - Button:hover background #BF8C2C

## 3. apps/admin_panel/templates/admin_panel/bookings_list.html

Extends base.html.

Content blocks:

Stats row (display grid, 4 columns, gap 16px, margin-bottom 32px):
Four .stat-card divs (background var(--surface), border var(--border), padding 20px, border-radius 4px):
- "TOTAL BOOKINGS" → {{ stats.total }}
- "PENDING" → {{ stats.pending }}
- "CONFIRMED THIS MONTH" → {{ stats.confirmed_this_month }}
- "COMPLETED" → {{ stats.completed }}
Each: label (11px, uppercase, letter-spaced, color var(--muted), margin-bottom 8px), number (32px, color var(--gold), font-weight 300)

Filter bar (display flex, gap 8px, margin-bottom 24px, flex-wrap wrap):
Filter links: All | Pending | Confirmed | Declined | Completed | Archived
Each is an <a href="?status=VALUE"> (or href="?" for All)
Active state (when current_filter matches): border-color var(--gold), color var(--gold)
Each link styled as pill: padding 6px 16px, border 1px solid var(--border), color var(--muted), font-size 12px, letter-spacing 0.05em
"All" is active when current_filter is None

Bookings table (if bookings list is not empty):
- Full width table, border-collapse collapse
- thead: background var(--surface), th: padding 12px 16px, text-align left, font-size 11px, uppercase, letter-spaced, color var(--muted), border-bottom 1px solid var(--border)
- tbody tr: border-bottom 1px solid var(--border), transition background 0.15s
- tbody tr:hover: background rgba(255,255,255,0.02)
- td: padding 14px 16px, font-size 13px, color var(--text)
- Columns: Date received | Client | Service | Preferred date | Status | View
- Date received: format the created_at string to show just date and time (e.g. "Jan 20, 2025")
- Service: use .title() display (capitalize first letter)
- Status: use badge span with class matching status (badge-pending etc.)
- View: <a href="/admin-panel/bookings/{{ b.id }}/">View →</a> in gold
- Table wraps in a div with overflow-x: auto for mobile

Empty state (if no bookings):
- Centered div, padding 80px 20px, color var(--muted)
- "No bookings yet" heading, subtext based on current_filter

Page heading row (margin-bottom 24px, display flex, justify-content space-between, align-items center):
- "Bookings" h1 (font-size 20px, font-weight 400, margin 0)
- Total count: "{{ bookings|length }} result{{ bookings|length|pluralize }}" in muted

## 4. apps/admin_panel/templates/admin_panel/booking_detail.html

Extends base.html.

Back link: "← All bookings" linking to /admin-panel/bookings/{% if current_filter %}?status={{ current_filter }}{% endif %}

Success banner (if show_success): 
- Green-tinted box (background rgba(93,202,165,0.1), border 1px solid rgba(93,202,165,0.3), color #5DCAA5, padding 12px 16px, margin-bottom 24px, font-size 13px)
- Text: "Booking updated successfully."
- If booking.google_calendar_event_id: add " Google Calendar event created."

Page heading (h1 20px, font-weight 400): booking.name

Two-column layout (display grid, grid-template-columns 1fr 320px, gap 24px):
- At <900px: single column

LEFT CARD — Client Details (.card):
Section label: "CLIENT DETAILS" (11px, uppercase, letter-spaced, color muted, margin-bottom 20px)
Detail rows (each: display flex, border-bottom 1px solid var(--border), padding 12px 0):
- Name, Email (as mailto: link), Phone (as tel: link)
- Service (capitalized), Preferred date, Submitted (created_at formatted)
- Message (if exists — full width row with pre-wrap white-space)
Label column: 35%, color muted, font-size 12px, uppercase, letter-spaced
Value column: 65%, color text, font-size 14px

RIGHT CARD — Actions (.card, position sticky, top 80px):
Section label: "UPDATE STATUS"
Current status badge (centered, margin-bottom 20px)
Form (POST method, {% csrf_token %}):
- <select name="status" style="width:100%...">
  - Options: Pending | Confirmed | Declined | Completed | Archived
  - Selected attribute on option matching booking.status
- Submit button "Update Status" (full width, background var(--gold), color #0f0f0f, border none, padding 12px, font-family inherit, font-size 13px, font-weight 500, cursor pointer, margin-top 12px)

If booking.google_calendar_event_id:
- Separator line
- "CALENDAR" label
- Link "View in Google Calendar →" (href: https://calendar.google.com, target _blank)
  Note: Google Calendar doesn't support deep linking to specific events by event ID in a simple URL,
  so just link to https://calendar.google.com

Status reference (small, collapsible or just shown):
Small section showing all statuses with their badge colors as a legend.

Make all templates responsive. At <600px, stats grid becomes 2 columns. At <400px, 1 column.
```

**Verification steps after Prompt 5:**
```bash
python manage.py runserver

# First: POST a test booking to have data
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Amara Okafor","email":"amara@test.com","phone":"+234 800 000 0000","service":"wedding","preferred_date":"2025-06-15","message":"Full day coverage"}'

# Then: Run init_db and create_admin
python scripts/init_db.py
python scripts/create_admin.py  # enter a test password

# Visit http://localhost:8000/admin-panel/login/
# → Login page renders with gold styling
# Log in with the password you set
# → Redirects to /admin-panel/bookings/
# → Stats row shows numbers, booking appears in table
# Click the booking → detail page renders correctly
# Update status → redirects back with success banner
```

---

---

# PROMPT 6 — Frontend: Homepage + Portfolio

```
Read docs/FRONTEND_SPEC.md entirely before writing any code. All design tokens, typography rules, and component patterns must be followed exactly.

Build the first two frontend pages for GlobalPerks inside the frontend/ directory.

## Shared requirements for ALL frontend HTML files

1. Google Fonts link in every <head>:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=IBM+Plex+Mono:wght@300;400;500&display=swap" rel="stylesheet">
```

2. CSS variables block in every page's <style>: all design tokens from FRONTEND_SPEC.md

3. Shared CSS: CSS reset (box-sizing, margin, padding), body styles, typography hierarchy, button styles (.btn, .btn-primary, .btn-ghost), nav styles

4. Navigation (copy to every page — consistent HTML):
- Fixed top, 72px height, z-index 100, background rgba(10,10,10,0.95), backdrop-filter blur(8px), border-bottom 1px solid var(--border)
- Left: .nav-brand — "GlobalPerks" in DM Serif Display, 22px, color var(--gold-light), with a 1px gold underline (border-bottom 1px solid var(--gold-dim), padding-bottom 2px)
- Center: ul.nav-links — Home · Portfolio · Services · About · Contact (IBM Plex Mono, 13px, letter-spaced)
- Right: "Book a Session" — .btn.btn-ghost styled as small nav button
- Active page link: color var(--gold-light)
- Mobile: hamburger at ≤768px. Clicking opens a full-screen overlay nav.
- Nav JS: scroll-triggered — adds class .scrolled (slight background change) when page scrolled > 50px

5. Footer (copy to every page):
- Dark surface, border-top 1px solid var(--border), padding 48px 24px
- Three columns (at mobile: stacked):
  Left: "GlobalPerks" brand + one-line tagline + copyright
  Center: Quick links list
  Right: "Follow" + three SVG social icons (Instagram, Pinterest, LinkedIn — simple geometric SVGs)
- Bottom border: 1px solid var(--border-gold)

## 1. frontend/index.html — Homepage

Build ALL 7 sections defined in FRONTEND_SPEC.md "index.html — Homepage":

HERO SECTION:
- 100vh, position relative
- Background: linear-gradient(160deg, #1A1411 0%, #0A0A0A 40%, #141410 100%)
- Add a subtle grid overlay texture using CSS: repeating-linear-gradient with very low opacity lines
- Content: max-width container, text left-aligned, vertically centered
- Eyebrow: "PREMIUM PHOTOGRAPHY · LAGOS" — 11px, letter-spacing 0.2em, color var(--gold-dim), IBM Plex Mono
- Headline: "Moments That" + line break + "Live Forever" — DM Serif Display, clamp(3rem, 8vw, 6rem), color var(--text-primary), line-height 1.0
- Gold rule: 60px wide, 1px, color var(--gold), margin 24px 0
- Subtext: "Portraits, weddings, and stories told with light." — IBM Plex Mono, 1.1rem, color var(--text-secondary), font-weight 300
- CTA row: two buttons side by side — "View Portfolio" (primary) and "Book a Session" (ghost)
- Scroll indicator: bottom-left, absolute positioned — thin line (2px, 40px tall, gold) + "scroll" text sideways (transform rotate(-90deg))

FEATURED WORK SECTION:
- padding 120px 0
- Section header: eyebrow "SELECTED WORK" + heading "Stories Worth Telling"
- Asymmetric photo grid: use CSS grid with specific template
  - Left column (2/3 width): 2 stacked photos (top: 3:2, bottom: 4:3)
  - Right column (1/3 width): 1 tall photo (full height of both left photos combined)
  - Gap: 12px
- Use <img src="https://picsum.photos/seed/gp1/800/600" alt="Portrait session"> style images
  Seeds to use: gp1, gp2, gp3, gp4, gp5, gp6 (use different seeds for variety)
- Each photo: position relative, overflow hidden, cursor pointer
- Hover effect: transform scale(1.03) on img, overlay appears with category label
- Overlay: absolute, inset 0, background rgba(10,10,10,0.7), opacity 0, transition 0.3s
  Shows: category (IBM Plex Mono, 11px, uppercase, letter-spaced, gold) + year
- "View full portfolio →" link below grid, right-aligned, gold

ABOUT TEASER SECTION:
- Two-column: text left (55%), image right (45%), gap 80px, align-items center
- Text side: eyebrow + heading "Eye for Detail, Heart for People" + 2-sentence bio
- Stats strip below bio: three items separated by gold lines — "150+" · "8 Years" · "12 Countries"
  Each: number in DM Serif Display 2rem gold, label below in monospace muted
- Image: picsum.photos/seed/gpabout/600/700, aspect-ratio 3/4, object-fit cover
- "Read My Story →" link

SERVICES OVERVIEW SECTION:
- Background var(--bg-surface), padding 120px 0
- Eyebrow + heading "Every Occasion, Captured"
- 5-column grid (at tablet: 3+2, at mobile: 1):
  Cards with: border 1px solid var(--border), padding 32px 24px, background var(--bg-card)
  Each card: unicode symbol (📷 🤵 💼 🎉 ✈️ → replace with simple CSS shapes or SVG icons), 
  service name in monospace, one-line description in muted, "From ₦X" pricing
  Hover: border-color var(--gold-dim), transform translateY(-4px)

TESTIMONIALS SECTION:
- Dark background, padding 120px 0
- Eyebrow + heading "What Clients Say"
- Three testimonial cards in a row (at mobile: stacked)
- Each card: large opening quote mark (DM Serif Display, 80px, gold, opacity 0.3), quote text, 
  divider, client name + shoot type
- Auto-rotate JS: every 5s, highlight active card with gold border

CTA BAND:
- Background var(--bg-surface), border-top 1px solid var(--border-gold), border-bottom 1px solid var(--border-gold)
- Centered content, padding 80px 24px
- Heading "Let's Create Something Beautiful" — DM Serif Display, 3rem
- Subtext one line
- "Book a Session" button (primary)

## 2. frontend/portfolio.html — Portfolio

Build sections: Page Hero (50vh) + Filter Bar + Gallery Grid + Lightbox.

GALLERY GRID:
- Masonry-style using CSS columns: 3 (desktop), 2 (tablet), 1 (mobile)
- 24 placeholder images total (picsum seeds: gp-p1 through gp-p24)
- Each .gallery-item: break-inside avoid, margin-bottom 12px, position relative, overflow hidden
- Add data-category="portraits|wedding|commercial|events|travel" attributes
  Distribute: 6 portraits, 5 weddings, 4 commercial, 5 events, 4 travel
- Hover: scale + overlay with category badge

FILTER JS:
- Click filter pill → hide all .gallery-items → show only matching data-category
- "all" shows everything
- Smooth fade: opacity transition on items

LIGHTBOX:
- Pure CSS/JS, no library
- Click image → creates full-screen overlay
- Overlay: fixed, inset 0, background rgba(0,0,0,0.95), z-index 1000, display flex, align-items center, justify-content center
- Content: max-width 90vw, max-height 90vh, img fills space
- Controls: prev/next arrows (40px circle buttons, left/right edges), close button (top-right)
- Caption: category + image number at bottom
- Keyboard: Escape closes, arrow keys navigate
- Click outside image closes
```

**Verification steps after Prompt 6:**
```bash
cd frontend
npx serve . -p 3000
# → Open http://localhost:3000/index.html
# → Hero section renders with dark background and gold text
# → All 7 sections visible
# → Nav is sticky and collapses on mobile
# → Open http://localhost:3000/portfolio.html
# → Gallery grid renders
# → Filter pills work (click Portraits — shows only portrait images)
# → Click an image — lightbox opens
# → Arrow keys navigate, Escape closes
```

---

---

# PROMPT 7 — Frontend: Services, About, Contact Pages

```
Read docs/FRONTEND_SPEC.md sections for services.html, about.html, and contact.html before writing any code.

Build the three remaining frontend pages. Use the exact same nav and footer HTML from index.html (copy verbatim — consistent HTML is critical for coherent styling).

## 1. frontend/services.html

Build all sections from FRONTEND_SPEC.md "services.html — Services":

SERVICES DETAIL (5 services, alternating layout):
For each service, create a two-column section:
- Portraits: image left, text right — "Portraits" heading, description, includes list, "from ₦150,000", CTA
- Weddings: image right, text left
- Commercial: image left, text right
- Events: image right, text left
- Travel: image left, text right
Image: picsum.photos with appropriate seeds, aspect-ratio 4/3
Include list items (using custom gold bullet — ::before with content:'—', color: var(--gold)):
  Portraits: Full edited gallery · Print-ready files · 2-hour session
  Weddings: Full day coverage · Second shooter available · Online gallery
  Commercial: Brand-aligned shots · Multiple looks · Commercial license
  Events: Real-time captures · Fast turnaround · Crowd and detail shots
  Travel: Destination coverage · Aerial if available · Storytelling focus

PROCESS SECTION:
- Dark background, 4 steps in a horizontal row (vertical on mobile)
- Step number: DM Serif Display, 4rem, color rgba(217,166,64,0.2) — ghosted
- Step title: bold, gold
- Description: muted
- Connector lines between steps (CSS border-top dashes)
- Steps: 01 Enquiry / 02 Consultation / 03 The Shoot / 04 Delivery

FAQ ACCORDION:
Questions:
1. How far in advance should I book?
2. Do you travel for shoots?
3. What's included in the final delivery?
4. How long does editing take?
5. Do you require a deposit?
6. Can I request specific shots?

Each: accordion item with question as button (cursor pointer, display flex, justify-content space-between)
Chevron SVG rotates 180deg when open
Answer panel: max-height 0 → max-height 200px transition, overflow hidden

## 2. frontend/about.html

BIO SECTION:
- Large image (picsum seed: gpabout2, 600x700) floating right with 40px margin
- 3–4 paragraph story (write compelling photographer copy — focus on passion for light, Lagos roots, global reach)
- Pull quote: italic DM Serif Display, 1.5rem, color var(--text-primary), 3px left border in gold, padding-left 24px, margin 32px 0

VALUES STRIP:
- Three items in a row with vertical gold dividers between them
- Each: "LIGHT" / "EMOTION" / "STORY" — DM Serif Display 2rem, then one sentence description below

CREDENTIALS (optional small grid):
- 4 items: Years Active · Sessions Completed · Countries · Awards
- Same stat card style as homepage

## 3. frontend/contact.html

CONTACT SPLIT (two-column):
Left column (contact info):
- "Let's Talk" heading
- Email: hello@globalperks.com (mailto link)
- Instagram: @globalperks (external link)
- Response time note: "I respond to all enquiries within 24 hours"
- Location note: "Based in Lagos · Shooting worldwide"
- Small decorative gold rule

Right column (booking form):
Build the complete booking form from FRONTEND_SPEC.md "Booking Form Specification":
- All fields: name, email, phone, service (select), preferred_date, message
- Client-side validation: required fields, email format check
- Form state management JS:
  - Loading state on submit: disable button, show "Sending..."
  - Success state: hide form, show success message
  - Error state: show inline field errors from API, or generic error message
- fetch() to backend:
  const BACKEND_URL = 'http://localhost:8000';  // Change for production
  
  On submit:
  1. Prevent default
  2. Validate all required fields — add .error class to invalid inputs, show error spans
  3. If valid: 
     - Set button text to "Sending..."
     - Disable all inputs
     - POST to ${BACKEND_URL}/api/bookings/ with JSON body
  4. On 201 response:
     - Hide form with opacity transition
     - Show #form-success div
  5. On 400 response:
     - Parse JSON errors
     - Show first error for each field beneath that input
     - Re-enable form
  6. On 500 or network error:
     - Show #form-error: "Something went wrong. Please try again or email us directly."
     - Re-enable form
     - Log error to console
```

**Verification steps after Prompt 7:**
```bash
# With serve running on port 3000:
# → http://localhost:3000/services.html
#   Alternating service sections render
#   Process steps show correctly
#   FAQ accordion opens/closes with animation
#
# → http://localhost:3000/about.html
#   Bio with floating image renders
#   Pull quote styled correctly
#
# → http://localhost:3000/contact.html
#   Two-column layout renders
#   Form fields all present
#   Try submitting empty form → validation errors appear
#   Try submitting with invalid email → email error appears
```

---

---

# PROMPT 8 — Wire Frontend to Backend (Full End-to-End)

```
This is the final integration prompt. Wire the frontend booking form to the live backend and confirm the complete end-to-end flow works.

## 1. Update CORS settings for local development
In backend/config/settings.py, ensure CORS_ALLOWED_ORIGINS includes the local frontend serve URL:
The .env file should have:
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://127.0.0.1:5500,http://localhost:5500

## 2. Update frontend/contact.html backend URL
In the form JS in contact.html, ensure:
const BACKEND_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : 'https://your-backend.onrender.com';  // placeholder — Magnus will replace with real URL

## 3. Add CORS preflight handling
In backend/config/settings.py add:
CORS_ALLOW_METHODS = ['GET', 'POST', 'OPTIONS']
CORS_ALLOW_HEADERS = ['Content-Type', 'Accept']

## 4. Add a health check endpoint
In config/urls.py, add a simple health check:
```python
from django.http import JsonResponse

def health(request):
    return JsonResponse({'status': 'ok', 'service': 'globalperks-backend'})

urlpatterns = [
    path('health/', health, name='health'),
    path('api/', include('apps.bookings.urls')),
    path('admin-panel/', include('apps.admin_panel.urls')),
]
```

## 5. Create a production deployment checklist file
Create docs/DEPLOYMENT.md (full content provided in DEPLOYMENT.md template in docs folder).

## 6. Final check — review all files for these common issues:
- Any hardcoded localhost URLs in Python files? Replace with env vars.
- Any missing {% csrf_token %} in admin forms? Add.
- Any print() statements left in Python? Replace with logging.
- Any TODO comments that should be resolved? Resolve or document.
- requirements.txt has all packages? Verify.
- .env.example has all required variables? Verify against settings.py.

## 7. Test the complete booking flow end-to-end:
Open frontend/contact.html in browser while backend is running.
Fill in all fields with valid data.
Submit → should see "Sending..." then success message.
Check Django terminal → should show booking saved log.
Visit http://localhost:8000/admin-panel/bookings/ → new booking appears.
Click booking → detail page renders.
Change status to Confirmed → page reloads with success banner.
(If Google Calendar configured: event should appear in calendar)
```

**Verification steps after Prompt 8:**
```bash
# Terminal 1: Backend
cd backend && python manage.py runserver

# Terminal 2: Frontend
cd frontend && npx serve . -p 3000

# In browser:
# 1. Open http://localhost:3000/contact.html
# 2. Fill form and submit
# 3. See success message
# 4. Visit http://localhost:8000/admin-panel/bookings/ (login first)
# 5. See new booking
# 6. Change status to Confirmed
# 7. See Google Calendar event (if configured)
# 
# Full flow complete. Site is ready for deployment to Render.
```

---

---

# Post-Build: Render Deployment Steps

After all 8 prompts complete successfully, deploy with these steps:

## Backend on Render

1. Push `backend/` to a GitHub repository
2. Create new Web Service on Render
3. Connect the GitHub repo
4. Set:
   - **Build command:** `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`
   - **Start command:** `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2`
5. Add all environment variables from `.env.example` with real values
6. Deploy → wait for build to succeed
7. Open Render shell → run:
   ```bash
   python scripts/init_db.py
   python scripts/create_admin.py
   ```
8. Note your backend URL: `https://your-service-name.onrender.com`

## Frontend on Render (Static Site)

1. Push `frontend/` to same or separate GitHub repository
2. Create new Static Site on Render
3. Connect the repo
4. Set:
   - **Publish directory:** `frontend`
   - No build command needed
5. Update `contact.html` JS: replace placeholder backend URL with real Render URL
6. Update backend `CORS_ALLOWED_ORIGINS` env var with frontend Render URL
7. Deploy

## Final smoke test
- Visit live frontend → submit a booking → see success
- Visit `https://your-backend.onrender.com/admin-panel/bookings/` → booking appears
- Log in and update status → all working
