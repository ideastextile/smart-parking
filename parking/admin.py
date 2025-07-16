from django.contrib import admin
from .models import Vehicle, ParkingRecord, ParkingSettings

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'vehicle_type', 'is_monthly_pass_holder', 'created_at')
    search_fields = ('license_plate',)
    list_filter = ('vehicle_type', 'is_monthly_pass_holder')

@admin.register(ParkingRecord)
class ParkingRecordAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'token_number', 'entry_time', 'exit_time', 'status', 'pass_expires')
    list_filter = ('status', 'entry_time', 'exit_time')
    search_fields = ('vehicle__license_plate', 'token_number')

@admin.register(ParkingSettings)
class ParkingSettingsAdmin(admin.ModelAdmin):
    list_display = ('barrier_open', 'last_data_clear')
