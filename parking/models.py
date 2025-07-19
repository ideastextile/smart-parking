from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import random
import string



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    parking_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.user.username






class Vehicle(models.Model):
    VEHICLE_TYPE_CHOICES = [
        ('car', 'Car'),
        ('motorcycle', 'Motorcycle'),
        ('others','others'),
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
    parking_name = models.CharField(max_length=100)
    # Revenue tracking fields
    parking_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('free', 'Free (Monthly Pass)')
    ], default='pending')
    
    def save(self, *args, **kwargs):
        if not self.token_number:
            self.token_number = self.generate_token()
        if self.vehicle.is_monthly_pass_holder and not self.pass_expires:
            # Set pass expiry to 30 days from now
            self.pass_expires = timezone.now() + timezone.timedelta(days=30)
            self.payment_status = 'free'
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
    
    def calculate_parking_fee(self):
        """Calculate parking fee based on duration and vehicle type using dynamic pricing"""
        if self.vehicle.is_monthly_pass_holder:
            return 0.00
        
        duration_hours = self.get_parking_duration() / 60
        
        # Get pricing configuration for the parking owner
        # Find the user who owns this parking record
        from django.contrib.auth.models import User
        try:
            # Get the first admin user or the user associated with this parking
            user = User.objects.filter(is_staff=True).first()
            if not user:
                user = User.objects.first()
            
            pricing_config = PricingConfig.get_pricing_for_user(user)
            
            # Get rate based on vehicle type
            if self.vehicle.vehicle_type == 'car':
                base_rate = float(pricing_config.car_price_per_hour)
            elif self.vehicle.vehicle_type == 'motorcycle':
                base_rate = float(pricing_config.motorcycle_price_per_hour)
            else:  # others
                base_rate = float(pricing_config.others_price_per_hour)
        except:
            # Fallback to default rates if pricing config fails
            if self.vehicle.vehicle_type == 'car':
                base_rate = 5.00
            elif self.vehicle.vehicle_type == 'motorcycle':
                base_rate = 3.00
            else:
                base_rate = 7.00
        
        # Minimum charge for first hour
        if duration_hours <= 1:
            return base_rate
        else:
            return base_rate * duration_hours
    
    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.token_number}"


class ParkingSettings(models.Model):
    """Settings for the parking system"""
    barrier_open = models.BooleanField(default=False)
    last_data_clear = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Parking Settings"
        verbose_name_plural = "Parking Settings"


class PricingConfig(models.Model):
    """Pricing configuration for different vehicle types"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car_price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    motorcycle_price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=3.00)
    others_price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=7.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pricing Configuration"
        verbose_name_plural = "Pricing Configurations"
    
    def __str__(self):
        return f"Pricing for {self.user.username}"
    
    @classmethod
    def get_pricing_for_user(cls, user):
        """Get or create pricing configuration for a user"""
        pricing, created = cls.objects.get_or_create(
            user=user,
            defaults={
                'car_price_per_hour': 5.00,
                'motorcycle_price_per_hour': 3.00,
                'others_price_per_hour': 7.00
            }
        )
        return pricing



class ReceiptNotice(models.Model):
    message = models.TextField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return "Receipt Footer Message"