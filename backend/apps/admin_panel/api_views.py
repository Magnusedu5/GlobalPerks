import logging
import os
import re
import uuid
import bcrypt
import shutil
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.core.turso import get_connection
from apps.bookings.services import TursoBookingService
from apps.gallery.services import TursoGalleryService
from apps.core.site_content_service import SiteContentService, SECTION_ORDER, SECTION_LABELS
from apps.core.calendar_service import create_calendar_event
from .jwt_auth import generate_token, admin_api_required

logger = logging.getLogger(__name__)

VALID_STATUSES = ['pending', 'confirmed', 'declined', 'completed', 'archived']


class AdminJwtDebugView(APIView):
    """Temporary: generate + verify a token in the same request to diagnose signature issues."""
    def get(self, request):
        from django.conf import settings as s
        token = generate_token(0)
        try:
            payload = verify_token(token)
            return Response({
                'ok': True,
                'key_prefix': s.SECRET_KEY[:8],
                'key_len': len(s.SECRET_KEY),
                'payload': payload,
            })
        except Exception as e:
            return Response({'ok': False, 'error': str(e), 'key_prefix': s.SECRET_KEY[:8]})


class AdminLoginView(APIView):
    def post(self, request):
        password = request.data.get('password', '')
        try:
            conn = get_connection()
            cursor = conn.execute("SELECT id, password_hash FROM admin_users LIMIT 1")
            row = cursor.fetchone()
            if not row:
                return Response({'error': 'no_admin'}, status=401)
            admin_id, stored_hash = row[0], row[1]
            if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                return Response({'token': generate_token(admin_id)})
            return Response({'error': 'invalid_password'}, status=401)
        except Exception as e:
            logger.error(f"Admin login error: {e}", exc_info=True)
            return Response({'error': 'server_error'}, status=500)


class AdminLogoutView(APIView):
    @admin_api_required
    def post(self, request):
        return Response({'message': 'logged_out'})


class AdminBookingsView(APIView):
    @admin_api_required
    def get(self, request):
        try:
            status_filter = request.GET.get('status')
            if status_filter not in VALID_STATUSES:
                status_filter = None
            service = TursoBookingService()
            return Response({
                'bookings': service.get_all_bookings(status_filter),
                'stats': service.get_stats(),
            })
        except Exception as e:
            logger.error(f"Admin bookings list error: {e}", exc_info=True)
            return Response({'error': 'server_error'}, status=500)


class AdminBookingDetailView(APIView):
    @admin_api_required
    def get(self, request, booking_id):
        try:
            booking = TursoBookingService().get_booking_by_id(booking_id)
            if not booking:
                return Response({'error': 'not_found'}, status=404)
            return Response({'booking': booking})
        except Exception as e:
            logger.error(f"Admin booking detail error: {e}", exc_info=True)
            return Response({'error': 'server_error'}, status=500)

    @admin_api_required
    def patch(self, request, booking_id):
        try:
            new_status = request.data.get('status', '')
            if new_status not in VALID_STATUSES:
                return Response({'error': 'invalid_status'}, status=400)
            service = TursoBookingService()
            updated = service.update_booking_status(booking_id, new_status)
            if new_status == 'confirmed' and not updated.get('google_calendar_event_id'):
                event_id = create_calendar_event(updated)
                if event_id:
                    service.update_calendar_event_id(booking_id, event_id)
            return Response({'booking': updated})
        except Exception as e:
            logger.error(f"Admin booking update error: {e}", exc_info=True)
            return Response({'error': 'server_error'}, status=500)


class AdminGalleriesView(APIView):
    @admin_api_required
    def get(self, request):
        try:
            service = TursoGalleryService()
            albums = service.get_all_albums()
            for a in albums:
                a['photo_count'] = service.get_photo_count(a['id'])
                a['cover_url'] = (
                    request.build_absolute_uri(settings.MEDIA_URL + a['cover_photo'])
                    if a.get('cover_photo') else None
                )
            return Response({'galleries': albums})
        except Exception as e:
            logger.error(f"Admin galleries list error: {e}", exc_info=True)
            return Response({'error': 'server_error'}, status=500)

    @admin_api_required
    def post(self, request):
        try:
            title       = request.data.get('title', '').strip()
            client_name = request.data.get('client_name', '').strip()
            client_email= request.data.get('client_email', '').strip()
            password    = request.data.get('password', '').strip()
            description = request.data.get('description', '').strip()
            shoot_date  = request.data.get('shoot_date', '').strip()
            custom_slug = request.data.get('slug', '').strip()

            errors = {}
            if not title:        errors['title'] = 'Title is required'
            if not client_name:  errors['client_name'] = 'Client name is required'
            if not password or len(password) < 4:
                errors['password'] = 'Password must be at least 4 characters'
            if errors:
                return Response({'errors': errors}, status=400)

            service = TursoGalleryService()
            base = custom_slug if custom_slug else title
            slug = re.sub(r'[^a-z0-9-]', '', base.lower().replace(' ', '-'))[:50]
            if not slug:
                return Response({'errors': {'slug': 'Could not generate a valid URL slug'}}, status=400)
            if service.slug_exists(slug):
                return Response({'errors': {'slug': f'"{slug}" is already taken'}}, status=400)

            album = service.create_album({
                'title': title, 'slug': slug, 'client_name': client_name,
                'client_email': client_email, 'password': password,
                'description': description, 'shoot_date': shoot_date,
            })
            return Response({'gallery': album}, status=201)
        except Exception as e:
            logger.error(f"Admin gallery create error: {e}", exc_info=True)
            return Response({'error': 'server_error'}, status=500)


class AdminGalleryDetailView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @admin_api_required
    def get(self, request, slug):
        try:
            service = TursoGalleryService()
            album = service.get_album_by_slug(slug)
            if not album:
                return Response({'error': 'not_found'}, status=404)
            photos = service.get_photos(album['id'])
            for p in photos:
                p['url'] = request.build_absolute_uri(settings.MEDIA_URL + p['filepath'])
            if album.get('cover_photo'):
                album['cover_url'] = request.build_absolute_uri(
                    settings.MEDIA_URL + album['cover_photo'])
            return Response({'gallery': album, 'photos': photos})
        except Exception as e:
            logger.error(f"Admin gallery detail error: {e}", exc_info=True)
            return Response({'error': 'server_error'}, status=500)

    @admin_api_required
    def patch(self, request, slug):
        try:
            service = TursoGalleryService()
            album = service.get_album_by_slug(slug)
            if not album:
                return Response({'error': 'not_found'}, status=404)
            if request.data.get('action') == 'toggle_active':
                return Response({'gallery': service.toggle_active(album['id'])})
            return Response({'error': 'unknown_action'}, status=400)
        except Exception as e:
            logger.error(f"Admin gallery patch error: {e}", exc_info=True)
            return Response({'error': 'server_error'}, status=500)

    @admin_api_required
    def delete(self, request, slug):
        try:
            service = TursoGalleryService()
            album = service.get_album_by_slug(slug)
            if not album:
                return Response({'error': 'not_found'}, status=404)
            gallery_dir = os.path.join(settings.MEDIA_ROOT, 'galleries', album['slug'])
            if os.path.exists(gallery_dir):
                shutil.rmtree(gallery_dir)
            service.delete_album(album['id'])
            return Response({'message': 'deleted'})
        except Exception as e:
            logger.error(f"Admin gallery delete error: {e}", exc_info=True)
            return Response({'error': 'server_error'}, status=500)


class AdminGalleryPhotosView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @admin_api_required
    def post(self, request, slug):
        try:
            service = TursoGalleryService()
            album = service.get_album_by_slug(slug)
            if not album:
                return Response({'error': 'not_found'}, status=404)

            files = request.FILES.getlist('photos')
            if not files:
                return Response({'error': 'no_files'}, status=400)

            gallery_dir = os.path.join(settings.MEDIA_ROOT, 'galleries', slug)
            os.makedirs(gallery_dir, exist_ok=True)
            existing = service.get_photo_count(album['id'])
            fs = FileSystemStorage(location=gallery_dir)
            added = 0

            for i, f in enumerate(files):
                ext = os.path.splitext(f.name)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                    continue
                safe = f"{uuid.uuid4().hex}{ext}"
                fs.save(safe, f)
                path = f"galleries/{slug}/{safe}"
                service.add_photo(album_id=album['id'], filename=f.name,
                                  filepath=path, sort_order=existing + i)
                if not album.get('cover_photo') and i == 0:
                    service.set_cover(album['id'], path)
                    album['cover_photo'] = path
                added += 1

            photos = service.get_photos(album['id'])
            for p in photos:
                p['url'] = request.build_absolute_uri(settings.MEDIA_URL + p['filepath'])
            return Response({'photos': photos, 'added': added})
        except Exception as e:
            logger.error(f"Admin photo upload error: {e}", exc_info=True)
            return Response({'error': 'server_error'}, status=500)


class AdminGalleryPhotoDeleteView(APIView):
    @admin_api_required
    def delete(self, request, slug, photo_id):
        try:
            service = TursoGalleryService()
            album = service.get_album_by_slug(slug)
            if not album:
                return Response({'error': 'not_found'}, status=404)
            photos = service.get_photos(album['id'])
            photo = next((p for p in photos if p['id'] == photo_id), None)
            if not photo:
                return Response({'error': 'photo_not_found'}, status=404)
            fp = os.path.join(settings.MEDIA_ROOT, photo['filepath'])
            if os.path.exists(fp):
                os.remove(fp)
            service.delete_photo(photo_id)
            return Response({'message': 'deleted'})
        except Exception as e:
            logger.error(f"Admin photo delete error: {e}", exc_info=True)
            return Response({'error': 'server_error'}, status=500)


class AdminCmsView(APIView):
    @admin_api_required
    def get(self, request):
        try:
            grouped = SiteContentService().get_all_grouped()
            sections = []
            for s in SECTION_ORDER:
                items = grouped.get(s, [])
                if not items:
                    continue
                for item in items:
                    item['preview_url'] = item['value'] if item['type'] == 'image' else ''
                sections.append({'key': s, 'label': SECTION_LABELS.get(s, s), 'items': items})
            return Response({'sections': sections})
        except Exception as e:
            logger.error(f"Admin CMS get error: {e}", exc_info=True)
            return Response({'error': 'server_error'}, status=500)


class AdminCmsTextView(APIView):
    @admin_api_required
    def post(self, request):
        try:
            updates = request.data.get('updates', {})
            if not isinstance(updates, dict):
                return Response({'error': 'invalid_payload'}, status=400)
            return Response({'updated': SiteContentService().bulk_update_text(updates)})
        except Exception as e:
            logger.error(f"Admin CMS text update error: {e}", exc_info=True)
            return Response({'error': 'server_error'}, status=500)


class AdminCmsImageView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @admin_api_required
    def post(self, request):
        try:
            key = request.data.get('key', '').strip()
            image_file = request.FILES.get('image')
            if not key:
                return Response({'error': 'missing_key'}, status=400)
            if not image_file:
                return Response({'error': 'missing_image'}, status=400)
            ext = os.path.splitext(image_file.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                return Response({'error': 'invalid_type'}, status=400)
            cms_dir = os.path.join(settings.MEDIA_ROOT, 'cms')
            os.makedirs(cms_dir, exist_ok=True)
            safe = f"{uuid.uuid4().hex}{ext}"
            FileSystemStorage(location=cms_dir).save(safe, image_file)
            url = request.build_absolute_uri(f"{settings.MEDIA_URL}cms/{safe}")
            SiteContentService().update_image(key, url)
            return Response({'url': url})
        except Exception as e:
            logger.error(f"Admin CMS image upload error: {e}", exc_info=True)
            return Response({'error': 'server_error'}, status=500)


class AdminCmsImageDeleteView(APIView):
    @admin_api_required
    def delete(self, request, key):
        try:
            SiteContentService().update_image(key, '')
            return Response({'message': 'deleted'})
        except Exception as e:
            logger.error(f"Admin CMS image delete error: {e}", exc_info=True)
            return Response({'error': 'server_error'}, status=500)
