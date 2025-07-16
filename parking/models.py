from django.db import models
from django.utils import timezone
import random
import string


class Vehicle(models.Model):
    VEHICLE_TYPE_CHOICES = [
        ('car', 'Car'),
        ('motorcycle', 'Motorcycle'),
    ]
    
    license_plate = models.CharField(max_length=20, unique=True)
    is_monthly_pass_holder = models.BooleanField(default=False)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, default='car')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.license_plate} ({self.get_vehicle_type_display()})"


class ParkingRecord(models.Model):
    STATUS_CHOICES = [
        ('parked', 'Currently Parked'),
        ('exited', 'Exited'),
    ]
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    token_number = models.CharField(max_length=20, unique=True)
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='parked')
    pass_expires = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.token_number:
            self.token_number = self.generate_token()
        if self.vehicle.is_monthly_pass_holder and not self.pass_expires:
            # Set pass expiry to 30 days from now
            self.pass_expires = timezone.now() + timezone.timedelta(days=30)
        super().save(*args, **kwargs)
    
    def generate_token(self):
        """Generate a unique 8-digit token number"""
        while True:
            token = ''.join(random.choices(string.digits, k=8))
            if not ParkingRecord.objects.filter(token_number=token).exists():
                return token
    
    def get_parking_duration(self):
        """Calculate parking duration in minutes"""
        if self.exit_time:
            duration = self.exit_time - self.entry_time
            return int(duration.total_seconds() / 60)
        else:
            duration = timezone.now() - self.entry_time
            return int(duration.total_seconds() / 60)
    
    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.token_number}"


class ParkingSettings(models.Model):
    """Settings for the parking system"""
    barrier_open = models.BooleanField(default=False)
    last_data_clear = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Parking Settings"
        verbose_name_plural = "Parking Settings"

