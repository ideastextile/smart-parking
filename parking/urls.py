from django.urls import path


from . import views
app_name = 'parking'

urlpatterns = [
    path('', views.home, name='home'),
    path('entry/', views.entry_page, name='entry'),
    path('exit/', views.exit_page, name='exit'),
    path('dashboard/', views.dashboard, name='dashboard'),
    #auth
    # path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    # path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
   

    # ✅ Keep only one entry route for form POST
    path('vehicle-entry/', views.vehicle_entry, name='vehicle_entry'),

    # ✅ Keep this for QR code exit API
    path('api/vehicle-exit/', views.vehicle_exit, name='vehicle_exit'),
    path('api/scan-qr-exit/', views.scan_qr_exit, name='scan_qr_exit'),
    path('api/clear-data/', views.clear_data, name='clear_data'),
]
