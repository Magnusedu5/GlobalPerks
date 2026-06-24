from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='admin-login'),
    path('logout/', views.logout_view, name='admin-logout'),
    path('bookings/', views.bookings_list_view, name='admin-bookings-list'),
    path('bookings/<int:booking_id>/', views.booking_detail_view, name='admin-booking-detail'),
    path('galleries/', views.galleries_list_view, name='admin-galleries-list'),
    path('galleries/create/', views.gallery_create_view, name='admin-gallery-create'),
    path('galleries/<int:album_id>/', views.gallery_detail_view, name='admin-gallery-detail'),
    path('galleries/<int:album_id>/delete/', views.gallery_delete_view, name='admin-gallery-delete'),
    path('cms/', views.cms_view, name='admin-cms'),
    path('cms/delete-image/<str:key>/', views.cms_delete_image_view, name='admin-cms-delete-image'),
]
