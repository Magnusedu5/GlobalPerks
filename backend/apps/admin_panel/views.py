import logging
import os
import re
import uuid
import bcrypt
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from apps.bookings.services import TursoBookingService
from apps.core.turso import get_connection
from apps.core.calendar_service import create_calendar_event
from apps.gallery.services import TursoGalleryService
from apps.core.site_content_service import SiteContentService, SECTION_LABELS, SECTION_ORDER
from .decorators import admin_required

logger = logging.getLogger(__name__)

VALID_STATUSES = ['pending', 'confirmed', 'declined', 'completed', 'archived']


def login_view(request):
    if request.method == 'GET':
        return render(request, 'admin_panel/login.html', {})

    if request.method == 'POST':
        try:
            password = request.POST.get('password', '')
            conn = get_connection()
            cursor = conn.execute("SELECT password_hash FROM admin_users LIMIT 1")
            row = cursor.fetchone()
            if not row:
                return render(request, 'admin_panel/login.html', {'error': 'No admin account configured'})
            stored_hash = row[0]
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                request.session['is_admin'] = True
                return redirect('/admin-panel/bookings/')
            else:
                return render(request, 'admin_panel/login.html', {'error': 'Invalid password'})
        except Exception as e:
            logger.error(f"Login error: {e}", exc_info=True)
            return render(request, 'admin_panel/login.html', {'error': 'Something went wrong. Please try again.'})

    return redirect('/admin-panel/login/')


def logout_view(request):
    if request.method == 'POST':
        request.session.flush()
        return redirect('/admin-panel/login/')
    return redirect('/admin-panel/login/')


@admin_required
def bookings_list_view(request):
    try:
        status_filter = request.GET.get('status', None)
        if status_filter not in VALID_STATUSES:
            status_filter = None
        service = TursoBookingService()
        bookings = service.get_all_bookings(status_filter)
        stats = service.get_stats()
        return render(request, 'admin_panel/bookings_list.html', {
            'bookings': bookings,
            'stats': stats,
            'current_filter': status_filter,
        })
    except Exception as e:
        logger.error(f"bookings_list_view error: {e}", exc_info=True)
        return HttpResponse("Error loading bookings.", status=500)


@admin_required
def booking_detail_view(request, booking_id):
    if request.method == 'GET':
        try:
            booking = TursoBookingService().get_booking_by_id(booking_id)
            if not booking:
                return HttpResponse("Booking not found.", status=404)
            show_success = request.GET.get('updated') == 'true'
            return render(request, 'admin_panel/booking_detail.html', {
                'booking': booking,
                'show_success': show_success,
            })
        except Exception as e:
            logger.error(f"booking_detail_view GET error: {e}", exc_info=True)
            return HttpResponse("Error loading booking.", status=500)

    if request.method == 'POST':
        try:
            new_status = request.POST.get('status', '')
            if new_status not in VALID_STATUSES:
                return redirect(f'/admin-panel/bookings/{booking_id}/?error=invalid_status')
            service = TursoBookingService()
            updated_booking = service.update_booking_status(booking_id, new_status)
            if new_status == 'confirmed' and not updated_booking.get('google_calendar_event_id'):
                event_id = create_calendar_event(updated_booking)
                if event_id:
                    service.update_calendar_event_id(booking_id, event_id)
            return redirect(f'/admin-panel/bookings/{booking_id}/?updated=true')
        except Exception as e:
            logger.error(f"booking_detail_view POST error: {e}", exc_info=True)
            return HttpResponse("Error updating booking.", status=500)

    return redirect('/admin-panel/bookings/')


@admin_required
def galleries_list_view(request):
    try:
        service = TursoGalleryService()
        albums = service.get_all_albums()
        for album in albums:
            album['photo_count'] = service.get_photo_count(album['id'])
        return render(request, 'admin_panel/galleries_list.html', {'albums': albums})
    except Exception as e:
        logger.error(f"Galleries list error: {e}", exc_info=True)
        return HttpResponse("Error loading galleries", status=500)


@admin_required
def gallery_create_view(request):
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

            errors = {}
            if not title:
                errors['title'] = 'Title is required'
            if not client_name:
                errors['client_name'] = 'Client name is required'
            if not password or len(password) < 4:
                errors['password'] = 'Password must be at least 4 characters'

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

            gallery_dir = os.path.join(settings.MEDIA_ROOT, 'galleries', album['slug'])
            os.makedirs(gallery_dir, exist_ok=True)

            existing_count = service.get_photo_count(album_id)
            fs = FileSystemStorage(location=gallery_dir)

            for i, f in enumerate(uploaded_files):
                ext = os.path.splitext(f.name)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                    continue
                safe_name = f"{uuid.uuid4().hex}{ext}"
                fs.save(safe_name, f)
                relative_path = f"galleries/{album['slug']}/{safe_name}"
                service.add_photo(
                    album_id=album_id,
                    filename=f.name,
                    filepath=relative_path,
                    sort_order=existing_count + i,
                )
                if not album['cover_photo'] and i == 0:
                    service.set_cover(album_id, relative_path)

            return redirect(f'/admin-panel/galleries/{album_id}/?uploaded=true')

        elif action == 'toggle_active':
            service.toggle_active(album_id)
            return redirect(f'/admin-panel/galleries/{album_id}/?updated=true')

        elif action == 'delete_photo':
            photo_id = int(request.POST.get('photo_id', 0))
            photos = service.get_photos(album_id)
            photo = next((p for p in photos if p['id'] == photo_id), None)
            if photo:
                file_path = os.path.join(settings.MEDIA_ROOT, photo['filepath'])
                if os.path.exists(file_path):
                    os.remove(file_path)
                service.delete_photo(photo_id)
            return redirect(f'/admin-panel/galleries/{album_id}/?updated=true')

    photos = service.get_photos(album_id)
    show_created = request.GET.get('created') == 'true'
    show_uploaded = request.GET.get('uploaded') == 'true'
    show_updated = request.GET.get('updated') == 'true'

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
    if request.method != 'POST':
        return redirect('/admin-panel/galleries/')
    try:
        service = TursoGalleryService()
        album = service.get_album_by_id(album_id)
        if album:
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


@admin_required
def cms_view(request):
    service = SiteContentService()
    saved_section = None
    saved_image = None
    error = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_text':
            section = request.POST.get('section', '')
            section_keys = service.get_section_keys(section)
            updates = {}
            for item in section_keys:
                if item['type'] == 'text':
                    val = request.POST.get(item['key'], None)
                    if val is not None:
                        updates[item['key']] = val
            service.bulk_update_text(updates)
            saved_section = section

        elif action == 'upload_image':
            key = request.POST.get('key', '')
            image_file = request.FILES.get('image')
            if not image_file:
                error = 'missing_image'
            else:
                ext = os.path.splitext(image_file.name)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                    error = 'invalid_type'
                else:
                    cms_dir = os.path.join(settings.MEDIA_ROOT, 'cms')
                    os.makedirs(cms_dir, exist_ok=True)
                    safe_name = f"{uuid.uuid4().hex}{ext}"
                    fs = FileSystemStorage(location=cms_dir)
                    fs.save(safe_name, image_file)
                    relative_path = f"cms/{safe_name}"
                    full_url = request.build_absolute_uri(settings.MEDIA_URL + relative_path)
                    service.update_image(key, full_url)
                    saved_image = key

    grouped = service.get_all_grouped()
    sections_list = []
    for s in SECTION_ORDER:
        items = grouped.get(s, [])
        if not items:
            continue
        for item in items:
            if item['type'] == 'image':
                item['preview_url'] = item['value'] if item['value'] else ''
        sections_list.append({
            'key': s,
            'label': SECTION_LABELS.get(s, s),
            'items': items,
            'has_text': any(i['type'] == 'text' for i in items),
        })

    return render(request, 'admin_panel/cms.html', {
        'sections_list': sections_list,
        'saved_section': saved_section,
        'saved_image': saved_image,
        'error': error,
    })


@admin_required
def cms_delete_image_view(request, key):
    if request.method == 'POST':
        SiteContentService().update_image(key, '')
    return redirect('/admin-panel/cms/')
