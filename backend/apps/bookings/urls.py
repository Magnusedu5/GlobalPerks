from django.urls import path
from .views import BookingCreateView, SiteContentView

urlpatterns = [
    path('bookings/', BookingCreateView.as_view(), name='booking-create'),
    path('site-content/', SiteContentView.as_view(), name='site-content'),
]
