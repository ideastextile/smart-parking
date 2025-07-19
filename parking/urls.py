from django.urls import path
from . import views

app_name = 'parking'

urlpatterns = [
    path('', views.home, name='home'),
    path('entry/', views.entry_page, name='entry'),
    path('vehicle-entry/', views.vehicle_entry, name='vehicle_entry'),
    path('exit/', views.exit_page, name='exit'),
    path('vehicle-exit/', views.vehicle_exit, name='vehicle_exit'),
    path('scan-qr-exit/', views.scan_qr_exit, name='scan_qr_exit'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('clear-data/', views.clear_data, name='clear_data'),
    path('live-table-data/', views.live_table_data, name='live_table_data'),
    path('download-backup/', views.download_backup, name='download_backup'),
    path('upload-backup/', views.upload_backup, name='upload_backup'),
    path('analytics/', views.analytics_dashboard, name='analytics'),
    path('pricing-settings/', views.pricing_settings, name='pricing_settings'),
    path('api/revenue-analytics/', views.revenue_analytics, name='revenue_analytics'),
    path('api/recent-exits/', views.recent_exits_api, name='recent_exits_api'),
    path('api/parking-prediction/', views.parking_prediction_api, name='parking_prediction_api'),
    path('api/vehicle-count-today/', views.vehicle_count_today_api, name='vehicle_count_today_api'),
    path('api/update-pricing/', views.update_pricing_api, name='update_pricing_api'),
    path('api/current-pricing/', views.get_current_pricing_api, name='current_pricing_api'),
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('login/', views.custom_login_view, name='login'),
]

