# GlobalPerks — Client Gallery Portal

Read this entire file before writing any code. This adds a complete Client Gallery
Portal to the already-built GlobalPerks project. Do not modify any existing files
unless explicitly instructed. Build everything new.

---

## What This Feature Does

Perfecta finishes editing a client's photos, logs into her admin dashboard, creates
an album, uploads the photos, and sets a password. The system generates a unique URL
like `/gallery/amara-portraits-2025`. She sends the client that link and password.

The client visits the URL, enters the password, and sees a full-screen cinematic
gallery experience — their name displayed, photos presented one at a time with
beautiful transitions, download option, and smooth navigation.

---

## Architecture Overview

```
New database tables:    albums, album_photos
New backend routes:     /api/gallery/<slug>/unlock/  (POST — verify password)
                        /api/gallery/<slug>/photos/  (GET — fetch photos, auth required)
New admin routes:       /admin-panel/galleries/              (list all albums)
                        /admin-panel/galleries/create/       (create new album)
                        /admin-panel/galleries/<id>/         (album detail + photo upload)
                        /admin-panel/galleries/<id>/delete/  (delete album)
New frontend page:      frontend/gallery.html  (the client-facing gallery experience)
File storage:           Photos uploaded to /media/galleries/<album_slug>/ on the server
```

---

## STEP 1 — Database Schema (Turso)

Add these two tables to `backend/apps/core/turso.py` inside the `init_db()` function.
Add them AFTER the existing CREATE TABLE statements. Do not remove existing tables.

```sql
CREATE TABLE IF NOT EXISTS albums (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    slug         TEXT NOT NULL UNIQUE,
    client_name  TEXT NOT NULL,
    client_email TEXT,
    password_hash TEXT NOT NULL,
    description  TEXT,
    shoot_date   TEXT,
    is_active    INTEGER NOT NULL DEFAULT 1,
    cover_photo  TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS album_photos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    album_id   INTEGER NOT NULL,
    filename   TEXT NOT NULL,
    filepath   TEXT NOT NULL,
    caption    TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
);
```

Run `python scripts/init_db.py` after adding these — it calls `init_db()` which now
creates these tables too.

---

## STEP 2 — Media Storage Setup

In `backend/config/settings.py`, add at the bottom:

```python
import os
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

In `backend/config/urls.py`, add media file serving in development:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('api/', include('apps.bookings.urls')),
    path('admin-panel/', include('apps.admin_panel.urls')),
    path('gallery-api/', include('apps.gallery.urls')),
    path('health/', health, name='health'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Create the media directory:
```
backend/media/galleries/   (create this folder, add a .gitkeep file inside)
```

Add to `.gitignore` (create if missing):
```
media/galleries/*
!media/galleries/.gitkeep
```

---

## STEP 3 — Gallery App

Create a new Django app: `backend/apps/gallery/`

Structure:
```
apps/gallery/
├── __init__.py
├── apps.py
├── urls.py
├── views.py       ← Public API views (DRF)
└── services.py    ← TursoGalleryService
```

Add `apps.gallery` to `INSTALLED_APPS` in `settings.py`.

### apps/gallery/services.py

`TursoGalleryService` class using `get_connection()` from `apps.core.turso`.
All queries use `?` parameterised statements.

```python
import os
import bcrypt
import logging
from apps.core.turso import get_connection

logger = logging.getLogger(__name__)

class TursoGalleryService:

    def _row_to_dict(self, cursor, row):
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

    def create_album(self, data: dict) -> dict:
        """
        data keys: title, slug, client_name, client_email, password,
                   description, shoot_date
        Hashes the password before storing.
        Returns the created album dict.
        """
        conn = get_connection()
        password_hash = bcrypt.hashpw(
            data['password'].encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        conn.execute("""
            INSERT INTO albums
                (title, slug, client_name, client_email, password_hash,
                 description, shoot_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data['title'],
            data['slug'],
            data['client_name'],
            data.get('client_email', ''),
            password_hash,
            data.get('description', ''),
            data.get('shoot_date', ''),
        ))
        conn.commit()
        cursor = conn.execute(
            "SELECT * FROM albums WHERE slug = ?", (data['slug'],)
        )
        return self._row_to_dict(cursor, cursor.fetchone())

    def get_all_albums(self) -> list:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT * FROM albums ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        return [self._row_to_dict(cursor, r) for r in rows]

    def get_album_by_slug(self, slug: str) -> dict | None:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT * FROM albums WHERE slug = ?", (slug,)
        )
        row = cursor.fetchone()
        return self._row_to_dict(cursor, row) if row else None

    def get_album_by_id(self, album_id: int) -> dict | None:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT * FROM albums WHERE id = ?", (album_id,)
        )
        row = cursor.fetchone()
        return self._row_to_dict(cursor, row) if row else None

    def verify_password(self, slug: str, password: str) -> bool:
        """Returns True if password matches, False otherwise."""
        album = self.get_album_by_slug(slug)
        if not album:
            return False
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                album['password_hash'].encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password check failed: {e}")
            return False

    def add_photo(self, album_id: int, filename: str, filepath: str,
                  caption: str = '', sort_order: int = 0) -> dict:
        conn = get_connection()
        conn.execute("""
            INSERT INTO album_photos
                (album_id, filename, filepath, caption, sort_order)
            VALUES (?, ?, ?, ?, ?)
        """, (album_id, filename, filepath, caption, sort_order))
        conn.commit()
        cursor = conn.execute(
            "SELECT * FROM album_photos WHERE album_id = ? ORDER BY sort_order",
            (album_id,)
        )
        rows = cursor.fetchall()
        return [self._row_to_dict(cursor, r) for r in rows]

    def get_photos(self, album_id: int) -> list:
        conn = get_connection()
        cursor = conn.execute("""
            SELECT * FROM album_photos
            WHERE album_id = ?
            ORDER BY sort_order ASC, created_at ASC
        """, (album_id,))
        rows = cursor.fetchall()
        return [self._row_to_dict(cursor, r) for r in rows]

    def delete_photo(self, photo_id: int) -> None:
        conn = get_connection()
        conn.execute("DELETE FROM album_photos WHERE id = ?", (photo_id,))
        conn.commit()

    def set_cover(self, album_id: int, filepath: str) -> None:
        conn = get_connection()
        conn.execute(
            "UPDATE albums SET cover_photo = ? WHERE id = ?",
            (filepath, album_id)
        )
        conn.commit()

    def toggle_active(self, album_id: int) -> dict:
        conn = get_connection()
        album = self.get_album_by_id(album_id)
        new_state = 0 if album['is_active'] else 1
        conn.execute(
            "UPDATE albums SET is_active = ? WHERE id = ?",
            (new_state, album_id)
        )
        conn.commit()
        return self.get_album_by_id(album_id)

    def delete_album(self, album_id: int) -> None:
        """Deletes album and all its photos from database. Files deleted separately."""
        conn = get_connection()
        conn.execute("DELETE FROM album_photos WHERE album_id = ?", (album_id,))
        conn.execute("DELETE FROM albums WHERE id = ?", (album_id,))
        conn.commit()

    def slug_exists(self, slug: str) -> bool:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT COUNT(*) FROM albums WHERE slug = ?", (slug,)
        )
        return cursor.fetchone()[0] > 0

    def get_photo_count(self, album_id: int) -> int:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT COUNT(*) FROM album_photos WHERE album_id = ?", (album_id,)
        )
        return cursor.fetchone()[0]
```

### apps/gallery/views.py (Public API — DRF)

Two endpoints. No authentication required — security is the per-gallery password.

```python
import json
import logging
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from .services import TursoGalleryService

logger = logging.getLogger(__name__)


class GalleryUnlockView(APIView):
    """
    POST /gallery-api/<slug>/unlock/
    Body: { "password": "..." }
    Returns: { "success": true, "album": { title, client_name, photo_count } }
    On fail: 401 { "error": "Incorrect password" }
    On not found: 404
    On inactive: 403
    """
    def post(self, request, slug):
        try:
            service = TursoGalleryService()
            album = service.get_album_by_slug(slug)
            if not album:
                return Response({'error': 'Gallery not found'}, status=404)
            if not album['is_active']:
                return Response({'error': 'This gallery is no longer available'}, status=403)
            password = request.data.get('password', '')
            if not service.verify_password(slug, password):
                return Response({'error': 'Incorrect password'}, status=401)
            # Set session flag so photos can be fetched
            request.session[f'gallery_unlocked_{slug}'] = True
            return Response({
                'success': True,
                'album': {
                    'title': album['title'],
                    'client_name': album['client_name'],
                    'description': album['description'],
                    'shoot_date': album['shoot_date'],
                    'photo_count': service.get_photo_count(album['id']),
                }
            })
        except Exception as e:
            logger.error(f"Gallery unlock error: {e}", exc_info=True)
            return Response({'error': 'Something went wrong'}, status=500)


class GalleryPhotosView(APIView):
    """
    GET /gallery-api/<slug>/photos/
    Requires session flag set by unlock endpoint.
    Returns: { "photos": [ { url, filename, caption } ... ] }
    """
    def get(self, request, slug):
        try:
            # Check session
            if not request.session.get(f'gallery_unlocked_{slug}'):
                return Response({'error': 'Authentication required'}, status=401)
            service = TursoGalleryService()
            album = service.get_album_by_slug(slug)
            if not album:
                return Response({'error': 'Gallery not found'}, status=404)
            if not album['is_active']:
                return Response({'error': 'Gallery not available'}, status=403)
            photos = service.get_photos(album['id'])
            photo_list = []
            for p in photos:
                # Build absolute URL for the photo
                filepath = p['filepath']
                url = request.build_absolute_uri(
                    settings.MEDIA_URL + filepath.replace('\\', '/')
                )
                photo_list.append({
                    'id': p['id'],
                    'url': url,
                    'filename': p['filename'],
                    'caption': p['caption'] or '',
                })
            return Response({'photos': photo_list, 'album': {
                'title': album['title'],
                'client_name': album['client_name'],
            }})
        except Exception as e:
            logger.error(f"Gallery photos error: {e}", exc_info=True)
            return Response({'error': 'Something went wrong'}, status=500)
```

### apps/gallery/urls.py

```python
from django.urls import path
from .views import GalleryUnlockView, GalleryPhotosView

urlpatterns = [
    path('<slug:slug>/unlock/', GalleryUnlockView.as_view(), name='gallery-unlock'),
    path('<slug:slug>/photos/', GalleryPhotosView.as_view(), name='gallery-photos'),
]
```

---

## STEP 4 — Admin Panel Gallery Views

Add gallery management views to `backend/apps/admin_panel/views.py`.
Import TursoGalleryService at the top of the file.

Also add these imports at the top of views.py:
```python
import os
import re
import uuid
from django.conf import settings
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
```

Add these five view functions:

```python
@admin_required
def galleries_list_view(request):
    """GET /admin-panel/galleries/ — list all albums with photo counts"""
    try:
        service = TursoGalleryService()
        albums = service.get_all_albums()
        # Add photo count to each album
        for album in albums:
            album['photo_count'] = service.get_photo_count(album['id'])
        return render(request, 'admin_panel/galleries_list.html', {'albums': albums})
    except Exception as e:
        logger.error(f"Galleries list error: {e}", exc_info=True)
        return HttpResponse("Error loading galleries", status=500)


@admin_required
def gallery_create_view(request):
    """GET renders form. POST creates album."""
    if request.method == 'GET':
        return render(request, 'admin_panel/gallery_create.html', {})

    if request.method == 'POST':
        try:
            title = request.POST.get('title', '').strip()
            client_name = request.POST.get('client_name', '').strip()
            client_email = request.POST.get('client_email', '').strip()
            password = request.POST.get('password', '').strip()
            description = request.POST.get('description', '').strip()
            shoot_date = request.POST.get('shoot_date', '').strip()
            custom_slug = request.POST.get('slug', '').strip()

            # Validation
            errors = {}
            if not title:
                errors['title'] = 'Title is required'
            if not client_name:
                errors['client_name'] = 'Client name is required'
            if not password or len(password) < 4:
                errors['password'] = 'Password must be at least 4 characters'

            # Generate or validate slug
            service = TursoGalleryService()
            if custom_slug:
                slug = re.sub(r'[^a-z0-9-]', '', custom_slug.lower().replace(' ', '-'))
            else:
                slug = re.sub(r'[^a-z0-9-]', '', title.lower().replace(' ', '-'))
                slug = slug[:50]

            if not slug:
                errors['slug'] = 'Could not generate a valid URL slug'
            elif service.slug_exists(slug):
                errors['slug'] = f'URL "{slug}" is already taken. Choose a different title or custom slug.'

            if errors:
                return render(request, 'admin_panel/gallery_create.html', {
                    'errors': errors,
                    'form_data': request.POST,
                })

            album = service.create_album({
                'title': title,
                'slug': slug,
                'client_name': client_name,
                'client_email': client_email,
                'password': password,
                'description': description,
                'shoot_date': shoot_date,
            })
            return redirect(f'/admin-panel/galleries/{album["id"]}/?created=true')

        except Exception as e:
            logger.error(f"Gallery create error: {e}", exc_info=True)
            return render(request, 'admin_panel/gallery_create.html', {
                'errors': {'general': 'Something went wrong. Please try again.'},
                'form_data': request.POST,
            })


@admin_required
def gallery_detail_view(request, album_id):
    """
    GET  — renders album detail with photo list and upload form
    POST — handles photo upload (multipart/form-data, field name: photos)
    """
    service = TursoGalleryService()
    album = service.get_album_by_id(album_id)
    if not album:
        return HttpResponse("Gallery not found", status=404)

    if request.method == 'POST':
        action = request.POST.get('action', 'upload')

        if action == 'upload':
            uploaded_files = request.FILES.getlist('photos')
            if not uploaded_files:
                return redirect(f'/admin-panel/galleries/{album_id}/?error=no_files')

            # Ensure directory exists
            gallery_dir = os.path.join(settings.MEDIA_ROOT, 'galleries', album['slug'])
            os.makedirs(gallery_dir, exist_ok=True)

            existing_count = service.get_photo_count(album_id)
            fs = FileSystemStorage(location=gallery_dir)

            for i, f in enumerate(uploaded_files):
                # Sanitise filename
                ext = os.path.splitext(f.name)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                    continue
                safe_name = f"{uuid.uuid4().hex}{ext}"
                fs.save(safe_name, f)
                # Store relative path from MEDIA_ROOT
                relative_path = f"galleries/{album['slug']}/{safe_name}"
                service.add_photo(
                    album_id=album_id,
                    filename=f.name,
                    filepath=relative_path,
                    sort_order=existing_count + i,
                )
                # Set first photo as cover if none set
                if not album['cover_photo'] and i == 0:
                    service.set_cover(album_id, relative_path)

            return redirect(f'/admin-panel/galleries/{album_id}/?uploaded=true')

        elif action == 'toggle_active':
            service.toggle_active(album_id)
            return redirect(f'/admin-panel/galleries/{album_id}/?updated=true')

        elif action == 'delete_photo':
            photo_id = int(request.POST.get('photo_id', 0))
            # Get photo to delete file
            photos = service.get_photos(album_id)
            photo = next((p for p in photos if p['id'] == photo_id), None)
            if photo:
                file_path = os.path.join(settings.MEDIA_ROOT, photo['filepath'])
                if os.path.exists(file_path):
                    os.remove(file_path)
                service.delete_photo(photo_id)
            return redirect(f'/admin-panel/galleries/{album_id}/?updated=true')

    # GET
    photos = service.get_photos(album_id)
    show_created = request.GET.get('created') == 'true'
    show_uploaded = request.GET.get('uploaded') == 'true'
    show_updated = request.GET.get('updated') == 'true'

    # Build full media URLs for photos
    for p in photos:
        p['url'] = settings.MEDIA_URL + p['filepath'].replace('\\', '/')

    gallery_url = f"/gallery/{album['slug']}"

    return render(request, 'admin_panel/gallery_detail.html', {
        'album': album,
        'photos': photos,
        'gallery_url': gallery_url,
        'show_created': show_created,
        'show_uploaded': show_uploaded,
        'show_updated': show_updated,
        'photo_count': len(photos),
    })


@admin_required
def gallery_delete_view(request, album_id):
    """POST only — deletes album, all its photos, and all files."""
    if request.method != 'POST':
        return redirect(f'/admin-panel/galleries/')
    try:
        service = TursoGalleryService()
        album = service.get_album_by_id(album_id)
        if album:
            # Delete all files
            gallery_dir = os.path.join(
                settings.MEDIA_ROOT, 'galleries', album['slug']
            )
            if os.path.exists(gallery_dir):
                import shutil
                shutil.rmtree(gallery_dir)
            service.delete_album(album_id)
        return redirect('/admin-panel/galleries/?deleted=true')
    except Exception as e:
        logger.error(f"Gallery delete error: {e}", exc_info=True)
        return redirect(f'/admin-panel/galleries/{album_id}/?error=delete_failed')
```

### Add gallery URLs to apps/admin_panel/urls.py

Add these four patterns to the existing urlpatterns list:

```python
path('galleries/', views.galleries_list_view, name='admin-galleries-list'),
path('galleries/create/', views.gallery_create_view, name='admin-gallery-create'),
path('galleries/<int:album_id>/', views.gallery_detail_view, name='admin-gallery-detail'),
path('galleries/<int:album_id>/delete/', views.gallery_delete_view, name='admin-gallery-delete'),
```

---

## STEP 5 — Admin Gallery HTML Templates

Create four new template files in `backend/apps/admin_panel/templates/admin_panel/`.
All extend `base.html`. Use the same design tokens as the existing admin templates.

### galleries_list.html

Extends base.html.

Content:
- Page header row: "Galleries" h1 + "Create New Gallery" button (links to /admin-panel/galleries/create/)
- Success banner if ?deleted=true: "Gallery deleted successfully."
- If no albums: empty state — "No galleries yet. Create your first one." with button.
- Grid of album cards (CSS grid, 3 cols desktop / 2 tablet / 1 mobile, gap 16px):

Each album card (.card style):
  - Cover photo thumbnail at top: if album.cover_photo, show as 200px tall image
    (object-fit: cover, full width). If none, show a placeholder div with
    background var(--surface) and centered camera icon (📷 or SVG).
  - Card body (padding 16px):
    - Album title (16px, color var(--text))
    - Client name (13px, color var(--muted))
    - Shoot date if exists (12px, color var(--muted))
    - Row: photo count badge + status badge (active/inactive)
    - Gallery URL (11px, color var(--gold), truncated): /gallery/{{ album.slug }}
  - Card footer (border-top, padding 12px 16px, display flex, gap 8px):
    - "Manage" button → /admin-panel/galleries/{{ album.id }}/
    - "View URL" button (copy link icon) — onclick copies
      window.location.origin + '/gallery/' + slug to clipboard

### gallery_create.html

Extends base.html. Back link to /admin-panel/galleries/.

Form (POST, method=post, enctype NOT needed here — no file upload on create):
- {% csrf_token %}
- Error display: if errors.general, show error banner

Fields:
- Album title (required): text input, name="title"
  Help text: "e.g. Amara & David Wedding 2025"
- Client name (required): text input, name="client_name"
- Client email (optional): email input, name="client_email"
  Help text: "Optional — for your records only"
- Shoot date (optional): date input, name="shoot_date"
- Description (optional): textarea rows=3, name="description"
  Placeholder: "Add any notes about this shoot..."
- Custom URL slug (optional): text input, name="slug"
  Help text: "Leave blank to auto-generate from title.
  Will appear as: globalperks.com/gallery/your-slug-here"
  Show any slug error below this field.
- Gallery password (required, min 4 chars): password input, name="password"
  Help text: "Share this password with your client so they can view their photos"

Show field-level errors beneath each input (color: red, font-size: 12px).
Preserve form_data values on validation failure.

Submit button: "Create Gallery" (full width, gold/terracotta fill)

### gallery_detail.html

Extends base.html.

Success banners (show if query param present):
- ?created=true  → "Gallery created. Now upload photos below."
- ?uploaded=true → "Photos uploaded successfully."
- ?updated=true  → "Gallery updated."

Page header: album.title h1 + status badge (Active/Inactive)

Info strip (3 columns):
- Client: album.client_name
- Shoot date: album.shoot_date or "—"
- Photos: photo_count

Gallery URL box (highlighted card, gold border):
- Label: "CLIENT GALLERY LINK"
- URL display: window.location.origin + gallery_url (large, copyable)
- "Copy Link" button — copies URL to clipboard via JS
- "Open Gallery" link — opens gallery_url in new tab
- Password reminder: "Password: Set on creation — share securely with your client"

Two-column layout below (photos left 65%, actions right 35%):

LEFT — Photo Grid:
- "PHOTOS" section label
- If no photos: "No photos yet. Upload below."
- Masonry-style grid (3 cols, gap 8px):
  Each photo: position relative, overflow hidden
  - <img> with object-fit cover, aspect-ratio 1, border-radius 4px
  - Hover overlay: delete button (×) shown on hover
  - Delete form: POST action="/admin-panel/galleries/{{ album.id }}/"
    hidden input name="action" value="delete_photo"
    hidden input name="photo_id" value="{{ p.id }}"
    button type="submit" — confirm with JS: "Delete this photo? This cannot be undone."

RIGHT — Actions (sticky top 80px):

Upload card (.card):
- "UPLOAD PHOTOS" section label
- Form: method=post, enctype="multipart/form-data", action="/admin-panel/galleries/{{ album.id }}/"
  {% csrf_token %}
  hidden input name="action" value="upload"
  - File input: name="photos", accept="image/jpeg,image/png,image/webp", multiple
  - Styled drop zone: dashed border var(--border), padding 32px, text-align center,
    cursor pointer, hover border-color var(--gold)
    Label text: "Click to select photos" + "JPG, PNG or WEBP · Multiple allowed"
  - Show selected file count via JS
  - Upload button: full width, gold fill

Toggle Active card (.card, margin-top 16px):
- Label: "GALLERY STATUS"
- Current status badge
- Form POST with action="toggle_active":
  Button: "Deactivate Gallery" if active / "Activate Gallery" if inactive
  Help text: "Inactive galleries show a 'not available' message to clients"

Danger Zone card (.card, margin-top 16px, border-color: rgba(226,75,74,0.3)):
- Label: "DANGER ZONE" (color: #E24B4A)
- "Delete Gallery" button (red border, red text)
- Form POST to /admin-panel/galleries/{{ album.id }}/delete/
  Confirm via JS: "Delete this entire gallery? All photos will be permanently deleted."

### gallery_create.html and galleries_list.html

Add "Galleries" link to the navigation area of base.html:
Find the nav in base.html and add a link to /admin-panel/galleries/ after the
existing "Bookings" link.

---

## STEP 6 — Frontend Gallery Page

Create `frontend/gallery.html` — the client-facing gallery experience.

This page is COMPLETELY DIFFERENT from the rest of the site. It is a full-screen
immersive experience. No standard nav. No footer. Just the photos.

### Page structure (two states)

**State 1: Password Gate** (shown on page load)
Full-screen centered layout. Dark background (#120A06).

Content (centered card, max-width 420px):
- GlobalPerks wordmark: Cormorant Garamond italic, 28px, color #D4A574
- "Your gallery is ready" — Playfair Display, 22px, color #FAF0E6
- Subtitle: "Enter the password Perfecta shared with you" — Lato 300, 14px, muted
- Password input (full width, dark surface, warm border, focus: terracotta border)
- "View My Photos" button (full width, burgundy)
- Error message area (hidden by default, red tint)
- Loading state: spinner on button during API call

**State 2: Gallery Experience** (shown after correct password)
Full-screen. No scroll. Pure cinematic immersion.

Layout layers (all position: fixed, inset: 0):

Layer 1 — Background (z-index: 0):
  Dark (#0A0604). The photo sits above this.

Layer 2 — Current photo (z-index: 1):
  <img> centered, max-height: 85vh, max-width: 90vw, object-fit: contain
  Transition: opacity 0.6s ease + subtle scale 1.02→1.0 on enter

Layer 3 — Gradient overlays (z-index: 2, pointer-events: none):
  Top: linear-gradient(to bottom, rgba(10,6,4,0.7) 0%, transparent 30%)
  Bottom: linear-gradient(to top, rgba(10,6,4,0.8) 0%, transparent 40%)

Layer 4 — Header UI (z-index: 10, position: fixed, top: 0, full width, padding 20px 32px):
  Left: GlobalPerks wordmark (italic Cormorant Garamond, 20px, caramel)
  Right: Download button (current photo) + photo counter "3 / 24"

Layer 5 — Footer UI (z-index: 10, position: fixed, bottom: 0, full width, padding 24px 32px):
  Left: Client name "Amara's Gallery" — Playfair Display italic, 18px, warm white
  Center: Progress dots (max 20 shown, others represented by smaller dots)
  Right: Nothing (or caption if photo has one)

Layer 6 — Navigation arrows (z-index: 10):
  Left arrow: fixed, left: 24px, vertically centered
  Right arrow: fixed, right: 24px, vertically centered
  Both: 48px circles, background rgba(255,255,255,0.08), border 1px solid rgba(255,255,255,0.15)
  Hover: background rgba(255,255,255,0.15)
  SVG chevron icons inside each

Layer 7 — Slideshow controls (z-index: 10, fixed, bottom: 80px, centered):
  Play/Pause button — toggles auto-advance (5s per photo)
  When playing: shows pause icon
  When paused: shows play icon

### Gallery JavaScript

The entire gallery logic lives in a <script> block at the bottom of gallery.html.

```javascript
// Configuration
const BACKEND_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : 'https://your-backend.onrender.com'; // UPDATE BEFORE DEPLOY

// Get slug from URL: /gallery/<slug>
const slug = window.location.pathname.split('/').filter(Boolean)[1];

let photos = [];
let currentIndex = 0;
let isPlaying = false;
let slideshowTimer = null;
let albumData = {};

// DOM references (assigned after DOMContentLoaded)
let passwordGate, galleryExperience, passwordInput,
    unlockBtn, unlockError, currentPhoto, photoCounter,
    clientNameEl, progressDots, prevBtn, nextBtn,
    playPauseBtn, downloadBtn;

// --- UNLOCK ---
async function unlockGallery() {
  const password = passwordInput.value.trim();
  if (!password) return;

  unlockBtn.textContent = 'Opening...';
  unlockBtn.disabled = true;
  unlockError.hidden = true;

  try {
    const res = await fetch(`${BACKEND_URL}/gallery-api/${slug}/unlock/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
      credentials: 'include',
    });
    const data = await res.json();

    if (res.ok && data.success) {
      albumData = data.album;
      await loadPhotos();
    } else {
      unlockError.textContent = data.error || 'Incorrect password. Please try again.';
      unlockError.hidden = false;
      unlockBtn.textContent = 'View My Photos';
      unlockBtn.disabled = false;
      passwordInput.value = '';
      passwordInput.focus();
    }
  } catch (err) {
    unlockError.textContent = 'Connection error. Please check your internet and try again.';
    unlockError.hidden = false;
    unlockBtn.textContent = 'View My Photos';
    unlockBtn.disabled = false;
  }
}

// --- LOAD PHOTOS ---
async function loadPhotos() {
  try {
    const res = await fetch(`${BACKEND_URL}/gallery-api/${slug}/photos/`, {
      credentials: 'include',
    });
    const data = await res.json();

    if (!res.ok) {
      showUnlockError('Could not load photos. Please refresh and try again.');
      return;
    }

    photos = data.photos;
    albumData = { ...albumData, ...data.album };

    // Transition from password gate to gallery
    passwordGate.style.opacity = '0';
    setTimeout(() => {
      passwordGate.style.display = 'none';
      galleryExperience.style.display = 'block';
      // Force reflow then fade in
      requestAnimationFrame(() => {
        galleryExperience.style.opacity = '1';
      });
    }, 400);

    // Set client name
    clientNameEl.textContent = `${albumData.client_name}'s Gallery`;

    // Preload first 3 images
    photos.slice(0, 3).forEach(p => {
      const img = new Image();
      img.src = p.url;
    });

    // Show first photo
    showPhoto(0);
    buildProgressDots();

  } catch (err) {
    showUnlockError('Failed to load gallery. Please refresh.');
  }
}

// --- SHOW PHOTO ---
function showPhoto(index) {
  if (index < 0) index = photos.length - 1;
  if (index >= photos.length) index = 0;
  currentIndex = index;

  // Fade out
  currentPhoto.style.opacity = '0';
  currentPhoto.style.transform = 'scale(1.02)';

  setTimeout(() => {
    currentPhoto.src = photos[index].url;
    currentPhoto.alt = photos[index].caption || `Photo ${index + 1}`;
    // Fade in
    currentPhoto.style.opacity = '1';
    currentPhoto.style.transform = 'scale(1)';
  }, 300);

  // Update counter
  photoCounter.textContent = `${index + 1} / ${photos.length}`;

  // Update progress dots
  document.querySelectorAll('.dot').forEach((dot, i) => {
    dot.classList.toggle('active', i === index);
  });

  // Update download button href
  downloadBtn.href = photos[index].url;
  downloadBtn.download = photos[index].filename || `photo-${index + 1}.jpg`;

  // Preload next
  if (photos[index + 1]) {
    const img = new Image();
    img.src = photos[index + 1].url;
  }
}

// --- NAVIGATION ---
function goNext() { showPhoto(currentIndex + 1); }
function goPrev() { showPhoto(currentIndex - 1); }

// --- SLIDESHOW ---
function toggleSlideshow() {
  isPlaying = !isPlaying;
  if (isPlaying) {
    playPauseBtn.innerHTML = pauseIcon();
    slideshowTimer = setInterval(goNext, 5000);
  } else {
    playPauseBtn.innerHTML = playIcon();
    clearInterval(slideshowTimer);
  }
}

// --- PROGRESS DOTS ---
function buildProgressDots() {
  progressDots.innerHTML = '';
  const max = Math.min(photos.length, 30);
  for (let i = 0; i < max; i++) {
    const dot = document.createElement('button');
    dot.className = 'dot';
    dot.setAttribute('aria-label', `Go to photo ${i + 1}`);
    dot.addEventListener('click', () => showPhoto(i));
    progressDots.appendChild(dot);
  }
}

// --- KEYBOARD NAV ---
document.addEventListener('keydown', e => {
  if (galleryExperience.style.display === 'none') return;
  if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); goNext(); }
  if (e.key === 'ArrowLeft') goPrev();
  if (e.key === 'Escape') { if (isPlaying) toggleSlideshow(); }
});

// --- TOUCH SWIPE ---
let touchStartX = 0;
galleryExperience.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; });
galleryExperience.addEventListener('touchend', e => {
  const dx = e.changedTouches[0].clientX - touchStartX;
  if (Math.abs(dx) > 50) { dx < 0 ? goNext() : goPrev(); }
});

// Icon helpers
function playIcon() {
  return `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <polygon points="5,3 19,12 5,21"/></svg>`;
}
function pauseIcon() {
  return `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`;
}

// --- INIT ---
document.addEventListener('DOMContentLoaded', () => {
  passwordGate      = document.getElementById('password-gate');
  galleryExperience = document.getElementById('gallery-experience');
  passwordInput     = document.getElementById('gallery-password');
  unlockBtn         = document.getElementById('unlock-btn');
  unlockError       = document.getElementById('unlock-error');
  currentPhoto      = document.getElementById('current-photo');
  photoCounter      = document.getElementById('photo-counter');
  clientNameEl      = document.getElementById('client-name');
  progressDots      = document.getElementById('progress-dots');
  prevBtn           = document.getElementById('prev-btn');
  nextBtn           = document.getElementById('next-btn');
  playPauseBtn      = document.getElementById('play-pause-btn');
  downloadBtn       = document.getElementById('download-btn');

  unlockBtn.addEventListener('click', unlockGallery);
  passwordInput.addEventListener('keydown', e => { if (e.key === 'Enter') unlockGallery(); });
  prevBtn.addEventListener('click', goPrev);
  nextBtn.addEventListener('click', goNext);
  playPauseBtn.addEventListener('click', toggleSlideshow);
  playPauseBtn.innerHTML = playIcon();

  galleryExperience.style.display = 'none';
  galleryExperience.style.opacity = '0';
  galleryExperience.style.transition = 'opacity 0.6s ease';

  if (!slug) {
    document.getElementById('unlock-error').textContent = 'Gallery not found.';
    document.getElementById('unlock-error').hidden = false;
  }
});
```

### gallery.html Full HTML Structure

Build the complete HTML file with this structure and the JS above.

All CSS is inline in a `<style>` block. Key styles:

```css
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 100%; height: 100%; overflow: hidden; background: #0A0604; }

/* Password gate */
#password-gate {
  position: fixed; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: #0A0604;
  transition: opacity 0.4s ease;
}
.unlock-card {
  width: 100%; max-width: 420px;
  padding: 48px 40px;
  background: #1C0E08;
  border: 1px solid #3D1F14;
}
.brand { font-family: 'Cormorant Garamond', Georgia, serif; font-style: italic;
         font-size: 28px; color: #D4A574; font-weight: 400; }
.unlock-heading { font-family: 'Playfair Display', Georgia, serif;
                  font-size: 22px; color: #FAF0E6; margin: 16px 0 8px; }
.unlock-sub { font-family: 'Lato', sans-serif; font-size: 14px;
              color: #C4A882; font-weight: 300; margin-bottom: 32px; }
.unlock-input {
  width: 100%; padding: 14px 16px;
  background: #120A06; border: 1px solid #3D1F14;
  color: #FAF0E6; font-family: 'Lato', sans-serif; font-size: 15px;
  margin-bottom: 12px; border-radius: 0; outline: none;
  transition: border-color 0.2s;
}
.unlock-input:focus { border-color: #C4753A; }
.unlock-btn {
  width: 100%; padding: 14px;
  background: #7A2E2E; color: #FAF0E6;
  border: none; font-family: 'Lato', sans-serif;
  font-size: 14px; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; cursor: pointer;
  transition: background 0.2s;
}
.unlock-btn:hover { background: #9B3A3A; }
.unlock-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.unlock-error {
  margin-top: 12px; padding: 10px 14px;
  background: rgba(226,75,74,0.1); border: 1px solid rgba(226,75,74,0.3);
  color: #F09595; font-family: 'Lato', sans-serif; font-size: 13px;
}

/* Gallery experience */
#gallery-experience { position: fixed; inset: 0; background: #0A0604; }
#current-photo {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%) scale(1);
  max-height: 85vh; max-width: 90vw; object-fit: contain;
  transition: opacity 0.35s ease, transform 0.35s ease;
  display: block; user-select: none; -webkit-user-drag: none;
}
.gradient-top {
  position: fixed; top: 0; left: 0; right: 0; height: 160px;
  background: linear-gradient(to bottom, rgba(10,6,4,0.85) 0%, transparent 100%);
  pointer-events: none; z-index: 2;
}
.gradient-bottom {
  position: fixed; bottom: 0; left: 0; right: 0; height: 220px;
  background: linear-gradient(to top, rgba(10,6,4,0.9) 0%, transparent 100%);
  pointer-events: none; z-index: 2;
}
.gallery-header {
  position: fixed; top: 0; left: 0; right: 0; z-index: 10;
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 32px;
}
.gallery-brand { font-family: 'Cormorant Garamond', Georgia, serif;
                 font-style: italic; font-size: 20px; color: #D4A574; }
.header-right { display: flex; align-items: center; gap: 16px; }
.photo-counter { font-family: 'Lato', sans-serif; font-size: 13px; color: #C4A882; }
.download-btn {
  font-family: 'Lato', sans-serif; font-size: 12px; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: #FAF0E6; text-decoration: none;
  border: 1px solid rgba(250,240,230,0.3); padding: 8px 16px;
  transition: border-color 0.2s, color 0.2s;
}
.download-btn:hover { border-color: #D4A574; color: #D4A574; }
.gallery-footer {
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 10;
  display: flex; align-items: flex-end; justify-content: space-between;
  padding: 24px 32px 28px;
}
.client-name { font-family: 'Playfair Display', Georgia, serif;
               font-style: italic; font-size: 18px; color: #FAF0E6; }
#progress-dots { display: flex; gap: 6px; align-items: center; }
.dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: rgba(250,240,230,0.3); border: none; cursor: pointer;
  transition: background 0.2s, transform 0.2s; padding: 0;
}
.dot.active { background: #D4A574; transform: scale(1.4); }
.dot:hover { background: rgba(250,240,230,0.6); }
.nav-btn {
  position: fixed; top: 50%; z-index: 10;
  width: 48px; height: 48px; border-radius: 50%;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.12);
  color: #FAF0E6; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.2s; transform: translateY(-50%);
}
.nav-btn:hover { background: rgba(255,255,255,0.15); }
#prev-btn { left: 24px; }
#next-btn { right: 24px; }
.play-pause-btn {
  position: fixed; bottom: 72px; left: 50%; transform: translateX(-50%);
  z-index: 10; width: 40px; height: 40px; border-radius: 50%;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.12);
  color: #FAF0E6; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.2s;
}
.play-pause-btn:hover { background: rgba(255,255,255,0.15); }
@media (max-width: 600px) {
  .gallery-header { padding: 16px 20px; }
  .gallery-footer { padding: 16px 20px 20px; }
  .gallery-brand { font-size: 16px; }
  #prev-btn { left: 12px; }
  #next-btn { right: 12px; }
}
```

HTML body content:
```html
<!-- Password Gate -->
<div id="password-gate">
  <div class="unlock-card">
    <div class="brand">GlobalPerks</div>
    <h1 class="unlock-heading">Your gallery is ready</h1>
    <p class="unlock-sub">Enter the password Perfecta shared with you</p>
    <input class="unlock-input" id="gallery-password" type="password"
           placeholder="Gallery password" autocomplete="current-password">
    <button class="unlock-btn" id="unlock-btn">View My Photos</button>
    <div class="unlock-error" id="unlock-error" hidden></div>
  </div>
</div>

<!-- Gallery Experience -->
<div id="gallery-experience">
  <div class="gradient-top"></div>
  <div class="gradient-bottom"></div>

  <img id="current-photo" src="" alt="Gallery photo">

  <header class="gallery-header">
    <div class="gallery-brand">GlobalPerks</div>
    <div class="header-right">
      <span class="photo-counter" id="photo-counter"></span>
      <a class="download-btn" id="download-btn" href="#" download>↓ Save</a>
    </div>
  </header>

  <footer class="gallery-footer">
    <div class="client-name" id="client-name"></div>
    <div id="progress-dots"></div>
    <div></div>
  </footer>

  <button class="nav-btn" id="prev-btn" aria-label="Previous photo">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <polyline points="15,18 9,12 15,6"/>
    </svg>
  </button>

  <button class="nav-btn" id="next-btn" aria-label="Next photo">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <polyline points="9,18 15,12 9,6"/>
    </svg>
  </button>

  <button class="play-pause-btn" id="play-pause-btn" aria-label="Play slideshow"></button>
</div>
```

---

## STEP 7 — Wire Up Frontend Gallery Link

In `frontend/contact.html` (or wherever the booking form is), do NOT add a gallery
link — the gallery URL is only shared privately by Perfecta.

However, the gallery page must be accessible. Since the frontend is static HTML,
the gallery page lives at `frontend/gallery.html` and must be served by a web server.

On Render static sites, URLs like `/gallery/amara-2025` need to serve `gallery.html`.
Add a `_redirects` file to the frontend folder:

```
/gallery/*  /gallery.html  200
```

This tells Render's static site to serve `gallery.html` for any `/gallery/*` URL
while keeping the slug accessible to the JavaScript via `window.location.pathname`.

---

## STEP 8 — Update CORS for Gallery API

In `backend/config/settings.py`, ensure SESSION_COOKIE_SAMESITE allows cross-origin
session cookies from the frontend. Add:

```python
SESSION_COOKIE_SAMESITE = 'None' if not DEBUG else 'Lax'
SESSION_COOKIE_SECURE = not DEBUG
```

Also ensure django-cors-headers allows credentials:

```python
CORS_ALLOW_CREDENTIALS = True
```

This is required because the gallery frontend (different origin from backend) needs
to send session cookies with the photos request.

---

## Verification Steps

After all steps are complete:

```bash
# 1. Run migrations (for new media settings) and start server
python manage.py runserver

# 2. Init new DB tables
python scripts/init_db.py

# 3. Log into admin, create a test gallery
# Visit http://localhost:8000/admin-panel/galleries/
# → "Create New Gallery" button visible
# → Create a gallery: title="Test Gallery", client="Test Client", password="test1234"
# → Redirected to gallery detail page with "Gallery created" banner
# → Gallery URL shown: /gallery/test-gallery

# 4. Upload test photos
# → On the gallery detail page, upload 3-5 JPG files
# → Photos appear in the grid after upload
# → Cover photo set automatically

# 5. Open the client gallery
# → Open http://localhost:3000/gallery.html in browser (via npx serve frontend -p 3000)
#    OR navigate to http://localhost:3000/gallery/test-gallery
# → Password gate shown — enter wrong password → red error shown
# → Enter "test1234" → gallery loads with photos
# → Photos display with cinematic transitions
# → Arrow keys navigate, swipe works on mobile
# → Play button starts slideshow
# → Download button saves current photo
# → Progress dots update with each photo

# 6. Confirm server still starts cleanly
python manage.py runserver  # no errors
```
