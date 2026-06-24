from django.urls import path
from .views import GalleryUnlockView, GalleryPhotosView

urlpatterns = [
    path('<slug:slug>/unlock/', GalleryUnlockView.as_view(), name='gallery-unlock'),
    path('<slug:slug>/photos/', GalleryPhotosView.as_view(), name='gallery-photos'),
]
