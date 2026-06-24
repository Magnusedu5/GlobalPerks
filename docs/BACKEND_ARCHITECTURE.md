# GlobalPerks Backend — Architecture Reference

## Project Structure

```
backend/
├── manage.py
├── requirements.txt
├── .env.example
├── .env                         ← not committed to git
├── Procfile                     ← Render start command
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── __init__.py
│   ├── bookings/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── services.py
│   ├── admin_panel/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── decorators.py
│   │   └── templates/
│   │       └── admin_panel/
│   │           ├── base.html
│   │           ├── login.html
│   │           ├── bookings_list.html
│   │           └── booking_detail.html
│   └── core/
│       ├── __init__.py
│       ├── apps.py
│       ├── turso.py
│       ├── email_service.py
│       └── calendar_service.py
└── scripts/
    ├── init_db.py
    └── create_admin.py
```

---

## Module Responsibilities

### config/settings.py

Key settings:
- `SECRET_KEY` — from `DJANGO_SECRET_KEY` env var
- `DEBUG` — from `DEBUG` env var, default `False`
- `ALLOWED_HOSTS` — from `ALLOWED_HOSTS` env var, split on `,`
- `INSTALLED_APPS` — includes `rest_framework`, `corsheaders`, all three apps
- `DATABASES` — Django default SQLite (`db.sqlite3`) for sessions ONLY
- `SESSION_COOKIE_HTTPONLY = True`
- `SESSION_COOKIE_SECURE = not DEBUG`
- `SESSION_COOKIE_SAMESITE = 'Strict'`
- `SESSION_COOKIE_AGE = 86400`
- `CORS_ALLOWED_ORIGINS` — from env var
- `STATIC_ROOT` — `BASE_DIR / 'staticfiles'`
- `STATICFILES_STORAGE` — WhiteNoise compressed
- `TEMPLATES` — configured to find templates in each app's `templates/` folder
- `REST_FRAMEWORK` — no authentication required on public endpoints

### apps/core/turso.py

**Singleton connection pattern:**
```python
import libsql, os

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
    conn.execute("""CREATE TABLE IF NOT EXISTS bookings (...)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS admin_users (...)""")
    conn.commit()
```

**Important:** libsql connections are not thread-safe in the same way as SQLAlchemy. For a low-traffic photographer site with `--workers 2` on Gunicorn, the singleton per-process is fine. Each Gunicorn worker gets its own connection.

### apps/core/email_service.py

Two functions, both wrapped in try/except:

```python
def send_booking_confirmation(booking_data: dict) -> None:
    """Sends auto-reply to client. Never raises."""

def send_booking_notification(booking_data: dict) -> None:
    """Sends new booking alert to photographer. Never raises."""
```

Both called from `BookingCreateView` inside `threading.Thread` to avoid blocking the API response.

### apps/core/calendar_service.py

```python
def create_calendar_event(booking: dict) -> str | None:
    """
    Creates a Google Calendar event for a confirmed booking.
    Returns the event ID string on success, None on any failure.
    Never raises.
    """
```

Called from `admin_panel/views.py` when status changes to `confirmed`.

### apps/bookings/services.py

`TursoBookingService` class — all methods use `get_connection()` and raw SQL:

```python
class TursoBookingService:
    def create_booking(self, data: dict) -> dict
    def get_all_bookings(self, status_filter: str = None) -> list[dict]
    def get_booking_by_id(self, booking_id: int) -> dict | None
    def update_booking_status(self, booking_id: int, new_status: str) -> dict
    def update_calendar_event_id(self, booking_id: int, event_id: str) -> None
    def get_stats(self) -> dict
    def _row_to_dict(self, cursor, row) -> dict  # private helper
```

**Row-to-dict pattern:**
libsql cursors have a `.description` property after execution that gives column names:
```python
def _row_to_dict(self, cursor, row):
    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, row))
```

### apps/bookings/serializers.py

`BookingSerializer(serializers.Serializer)` — NOT a ModelSerializer since there's no Django model.

Validates: name, email, phone, service (choice), preferred_date (DateField), message (optional).

Note: `preferred_date` comes in as a `datetime.date` object from DRF's `DateField`. Convert to string before passing to Turso: `str(validated_data['preferred_date'])`.

### apps/bookings/views.py

`BookingCreateView(APIView)`:
- POST only
- Validates → creates booking → fires emails in threads → returns 201

```python
class BookingCreateView(APIView):
    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        try:
            data = serializer.validated_data
            data['preferred_date'] = str(data['preferred_date'])
            booking = TursoBookingService().create_booking(data)
            # Fire emails in background threads
            threading.Thread(target=send_booking_confirmation, args=(booking,), daemon=True).start()
            threading.Thread(target=send_booking_notification, args=(booking,), daemon=True).start()
            return Response({'success': True, 'message': 'Booking received'}, status=201)
        except Exception as e:
            logger.error(f"Booking creation failed: {e}")
            return Response({'error': 'Something went wrong. Please try again.'}, status=500)
```

### apps/admin_panel/decorators.py

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

### apps/admin_panel/views.py

Five function-based views:
1. `login_view` — GET renders form, POST authenticates
2. `logout_view` — POST only, flushes session
3. `bookings_list_view` — GET, @admin_required
4. `booking_detail_view` — GET + POST, @admin_required
5. (logout is POST-only for CSRF protection)

**Status update flow in `booking_detail_view`:**
```python
if request.method == 'POST':
    new_status = request.POST.get('status')
    valid_statuses = ['pending', 'confirmed', 'declined', 'completed', 'archived']
    if new_status not in valid_statuses:
        # return error
    
    service = TursoBookingService()
    booking = service.update_booking_status(booking_id, new_status)
    
    if new_status == 'confirmed' and not booking.get('google_calendar_event_id'):
        event_id = create_calendar_event(booking)
        if event_id:
            service.update_calendar_event_id(booking_id, event_id)
    
    return redirect(f'/admin-panel/bookings/{booking_id}/?updated=true')
```

---

## Admin Template Hierarchy

```
admin_panel/base.html           ← Shared layout: nav, head, CSS variables
admin_panel/login.html          ← Standalone (no base — different layout)
admin_panel/bookings_list.html  ← extends base.html
admin_panel/booking_detail.html ← extends base.html
```

`base.html` provides:
- `<head>` with title block, Google Fonts, inline CSS with design tokens
- Fixed top nav with "GlobalPerks Admin" and sign-out button
- Main content wrapper
- Flash message support

---

## Security Checklist

- [x] CSRF tokens on all admin HTML forms (`{% csrf_token %}`)
- [x] Session cookie HttpOnly + Secure in production
- [x] Admin password stored as bcrypt hash only
- [x] SQL queries use parameterised statements (`?` placeholders)
- [x] CORS restricted to allowed origins only
- [x] DEBUG=False in production
- [x] SECRET_KEY from environment variable
- [x] No sensitive data in logs (no passwords, no full tokens)
- [x] Email/calendar failures are silent (no data leakage in errors)

---

## Dependencies (requirements.txt)

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

---

## Setup Commands (Development)

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and fill in env vars
cp .env.example .env

# 4. Create Django session tables (SQLite)
python manage.py migrate

# 5. Create Turso tables
python scripts/init_db.py

# 6. Create admin password
python scripts/create_admin.py

# 7. Run development server
python manage.py runserver
```

---

## Setup Commands (Render Production)

**Build command:**
```
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
```

**Start command:**
```
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2
```

**One-time shell commands after first deploy:**
```bash
python scripts/init_db.py
python scripts/create_admin.py
```
