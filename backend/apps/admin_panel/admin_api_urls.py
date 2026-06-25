from django.urls import path
from . import api_views

urlpatterns = [
    path('login/',                                    api_views.AdminLoginView.as_view()),
    path('logout/',                                   api_views.AdminLogoutView.as_view()),
    path('bookings/',                                 api_views.AdminBookingsView.as_view()),
    path('bookings/<int:booking_id>/',                api_views.AdminBookingDetailView.as_view()),
    path('galleries/',                                api_views.AdminGalleriesView.as_view()),
    path('galleries/<str:slug>/',                     api_views.AdminGalleryDetailView.as_view()),
    path('galleries/<str:slug>/photos/',              api_views.AdminGalleryPhotosView.as_view()),
    path('galleries/<str:slug>/photos/<int:photo_id>/', api_views.AdminGalleryPhotoDeleteView.as_view()),
    path('cms/',                                      api_views.AdminCmsView.as_view()),
    path('cms/text/',                                 api_views.AdminCmsTextView.as_view()),
    path('cms/image/',                                api_views.AdminCmsImageView.as_view()),
    path('cms/image/<str:key>/',                      api_views.AdminCmsImageDeleteView.as_view()),
]
