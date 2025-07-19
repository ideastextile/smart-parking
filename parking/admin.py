from django.contrib import admin
from .models import Vehicle, ParkingRecord, ParkingSettings, Profile, PricingConfig , ReceiptNotice

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'parking_name', 'phone', 'contact_number']
    search_fields = ['user__username', 'user__email', 'parking_name']
    list_filter = ['parking_name']

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'vehicle_type', 'is_monthly_pass_holder', 'created_at')
    search_fields = ('license_plate',)
    list_filter = ('vehicle_type', 'is_monthly_pass_holder')

@admin.register(ParkingRecord)
class ParkingRecordAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'token_number', 'entry_time', 'exit_time', 'status', 'parking_name')
    list_filter = ('status', 'entry_time', 'exit_time', 'parking_name')
    search_fields = ('vehicle__license_plate', 'token_number', 'parking_name')

@admin.register(ParkingSettings)
class ParkingSettingsAdmin(admin.ModelAdmin):
    list_display = ('barrier_open', 'last_data_clear')

@admin.register(PricingConfig)
class PricingConfigAdmin(admin.ModelAdmin):
    list_display = ('user', 'car_price_per_hour', 'motorcycle_price_per_hour', 'others_price_per_hour')
    list_filter = ('user',)

@admin.register(ReceiptNotice)
class ReceiptNoticeAdmin(admin.ModelAdmin):
    list_display = ('message', 'active')