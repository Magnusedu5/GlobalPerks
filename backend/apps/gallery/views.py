import time
import jwt
import logging
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from .services import TursoGalleryService

logger = logging.getLogger(__name__)

GALLERY_TOKEN_TTL = 86400 * 7  # 7 days


def _make_gallery_token(slug: str) -> str:
    now = int(time.time())
    return jwt.encode(
        {'sub': slug, 'type': 'gallery', 'iat': now, 'exp': now + GALLERY_TOKEN_TTL},
        settings.SECRET_KEY, algorithm='HS256',
    )


def _verify_gallery_token(token: str, slug: str) -> bool:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload.get('type') == 'gallery' and payload.get('sub') == slug
    except jwt.InvalidTokenError:
        return False


class GalleryUnlockView(APIView):
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
            token = _make_gallery_token(slug)
            return Response({
                'success': True,
                'gallery_token': token,
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
    def get(self, request, slug):
        try:
            auth = request.headers.get('Authorization', '')
            token = auth[7:] if auth.startswith('Bearer ') else request.GET.get('token', '')
            if not token or not _verify_gallery_token(token, slug):
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
                filepath = p['filepath']
                if filepath.startswith('http'):
                    url = filepath
                else:
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
