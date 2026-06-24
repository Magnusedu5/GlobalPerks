from pathlib import Path
from django.urls import path, include
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.conf.urls.static import static


def health(request):
    return JsonResponse({'status': 'ok', 'service': 'globalperks-backend'})


def gallery_page(request, slug):
    """Serves frontend/gallery.html for /gallery/<slug> in development."""
    gallery_html = Path(settings.BASE_DIR).parent / 'frontend' / 'gallery.html'
    try:
        return HttpResponse(gallery_html.read_text(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse('Gallery page not found', status=404)


urlpatterns = [
    path('health/', health, name='health'),
    path('api/', include('apps.bookings.urls')),
    path('admin-panel/', include('apps.admin_panel.urls')),
    path('gallery-api/', include('apps.gallery.urls')),
    path('gallery/<slug:slug>', gallery_page, name='gallery-page'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
