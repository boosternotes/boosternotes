from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from myapp import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('signup/', views.signup, name='signup'),
    path(
        'logout/',
        auth_views.LogoutView.as_view(next_page=reverse_lazy('home')),
        name='logout'
    ),
    #user management
    path('users/add/', views.add_user, name='add_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),

     # Notifications
    path('notifications/', views.notifications_section, name='notifications_section'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),

    #coupons
    path('coupon_list', views.coupon_list, name='coupon_list'),
    path('delete/<int:pk>/', views.coupon_delete, name='coupon_delete'),
    path('toggle/<int:pk>/', views.coupon_toggle_active, name='coupon_toggle_active'),

    #category
    path('category_list', views.category_list, name='category_list'),
    path('delete/<int:pk>/', views.category_delete, name='category_delete'),
    path('toggle/<int:pk>/', views.coupon_toggle_active, name='category_toggle_active'),
    
     # Main dashboard
    
    # Navbar
    path('navbar/', views.navbar_custom, name='navbar_custom'),
    
    # Banner
    path('banner/', views.banner_custom, name='banner_custom'),
    
    # Stats
    path('stats/', views.stats_custom, name='stats_custom'),
    path('stats/edit/<int:pk>/', views.stats_edit, name='stats_edit'),
    path('stats/delete/<int:pk>/', views.stats_delete, name='stats_delete'),
    
    # About
    path('about/', views.about_custom, name='about_custom'),

    path('footer/', views.footer_custom, name='footer_custom'),

     # E-Library
    path('elibrary/', views.elibrary_dashboard, name='elibrary_dashboard'),
    path('elibrary/add/', views.elibrary_add, name='elibrary_add'),
    path('elibrary/edit/<uuid:pk>/', views.elibrary_edit, name='elibrary_edit'),
    path('elibrary/delete/<uuid:id>/', views.elibrary_delete, name='elibrary_delete'),
    path('elibrary/<uuid:pk>/upload-pdf/', views.elibrary_upload_pdf, name='elibrary_upload_pdf'),
    path('elibrary/pdf/delete/<uuid:pk>/', views.elibrary_pdf_delete, name='elibrary_pdf_delete'),

    path('hard-books/', views.hard_books_list, name='hard_books_list'),
    path('hard-books/add/', views.hard_book_add, name='hard_book_add'),
    path('hard-books/edit/<uuid:pk>/', views.hard_book_edit, name='hard_book_edit'),
    path('hard-books/delete/<uuid:pk>/', views.hard_book_delete, name='hard_book_delete'),
    path('hard-books/image-delete/<uuid:pk>/', views.hard_book_image_delete, name='hard_book_image_delete'),
    path('search/', views.search, name='search'),  # Add this line


      # Coupon System
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('elibrary/<uuid:pk>/', views.elibrary_detail, name='elibrary_detail'),

    
    
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)