from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from django.db import models
from django.template.loader import render_to_string
from parking.models import ParkingRecord, Profile, PricingConfig
from .forms import ProfileForm
from .models import Profile
import os
from django.http import JsonResponse, HttpResponse
from django.core import serializers
# from parking.utils import get_navbar_context
from .models import ParkingRecord, Vehicle
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

import json
import qrcode
import io
import base64
import uuid
import csv
from .models import ParkingRecord
from .models import Vehicle, ParkingRecord, ParkingSettings
from io import BytesIO
import datetime
from django.core.serializers import serialize


def get_navbar_context(user):
    """Get context data for navbar"""
    if user.is_authenticated:
        try:
            profile = user.profile
            return {
                'currently_parked': ParkingRecord.objects.filter(status='parked', parking_name=profile.parking_name).count()
            }
        except Profile.DoesNotExist:
            pass
    return {
        'currently_parked': 0
    }

@login_required
def home(request):
    """Home page with dashboard overview"""
    # Get user profile
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    
    # Get current statistics filtered by user's parking_name
    currently_parked = ParkingRecord.objects.filter(status='parked', parking_name=profile.parking_name).count()
    today = timezone.now().date()
    total_today = ParkingRecord.objects.filter(entry_time__date=today, parking_name=profile.parking_name).count()
    
    # Calculate average parking time for exited vehicles today
    exited_today = ParkingRecord.objects.filter(
        entry_time__date=today, 
        status='exited',
        parking_name=profile.parking_name
    )
    avg_minutes = 0
    if exited_today.exists():
        total_minutes = sum([record.get_parking_duration() for record in exited_today])
        avg_minutes = total_minutes // exited_today.count()
    
    context = {
        'currently_parked': currently_parked,
        'total_today': total_today,
        'avg_minutes': avg_minutes,
    }
    context.update(get_navbar_context(request.user))
    return render(request, 'parking/home.html', context)


@login_required
def entry_page(request):
    """Vehicle entry page"""
    # Get user profile
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    
    context = get_navbar_context(request.user)
    
    # Get current user's parking name
    parking_name = profile.parking_name

    # Get vehicles filtered by type and pass type
    def get_vehicle_data(vehicle_type, is_monthly):
        return ParkingRecord.objects.filter(
            vehicle__vehicle_type=vehicle_type,
            vehicle__is_monthly_pass_holder=is_monthly,
            parking_name=parking_name
        ).order_by('-entry_time')

    context.update({
        'monthly_car': get_vehicle_data('car', True),
        'regular_car': get_vehicle_data('car', False),
        'monthly_motorcycle': get_vehicle_data('motorcycle', True),
        'regular_motorcycle': get_vehicle_data('motorcycle', False),
        'monthly_others': get_vehicle_data('others', True),
        'regular_others': get_vehicle_data('others', False),
    })

    return render(request, 'parking/entry.html', context)


def generate_token():
    return str(uuid.uuid4())[:8].upper()


@csrf_exempt
@login_required
def vehicle_entry(request):
    if request.method == 'POST':
        try:
            license_plate = request.POST.get('license_plate', '').upper().strip()
            is_monthly_pass = request.POST.get('is_monthly_pass') == 'on'
            vehicle_type = request.POST.get('vehicle_type', 'car')
            notice = ReceiptNotice.objects.filter(active=True).first()

            if not license_plate:
                return JsonResponse({'error': 'License plate is required'}, status=400)

            if vehicle_type not in ["car", "motorcycle", "others"]:
                vehicle_type = "car"

            # Check if vehicle is already parked
            existing = ParkingRecord.objects.filter(
                vehicle__license_plate=license_plate,
                status='parked'
            ).first()
            if existing:
                return JsonResponse({'error': 'Vehicle is already parked'}, status=400)

            # Create or update vehicle
            vehicle, created = Vehicle.objects.get_or_create(
                license_plate=license_plate,
                defaults={'is_monthly_pass_holder': is_monthly_pass, 'vehicle_type': vehicle_type}
            )

            if not created:
                vehicle.is_monthly_pass_holder = is_monthly_pass
                vehicle.vehicle_type = vehicle_type
                vehicle.save()

            # ✅ Get user profile (to access parking_name)
            profile = request.user.profile

            # ✅ Create parking record with parking_name
            parking_record = ParkingRecord.objects.create(
                vehicle=vehicle,
                token_number=generate_token(),
                entry_time=timezone.now(),
                status='parked',
                parking_name=profile.parking_name
            )

            # ✅ Generate QR data
            qr_data = {
                'license_plate': license_plate,
                'token_number': parking_record.token_number,
                'entry_time': parking_record.entry_time.isoformat(),
                'vehicle_type': vehicle_type
            }

            # ✅ Generate QR code image
            qr = qrcode.make(json.dumps(qr_data))
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            qr_image = base64.b64encode(buffer.getvalue()).decode()

            # ✅ Render receipt template
            return render(request, 'parking/entry_receipt.html', {
                'car_number': license_plate,
                'vehicle_type': vehicle_type,
                'token_id': parking_record.token_number,
                'entry_time': parking_record.entry_time,
                'is_monthly_pass': is_monthly_pass,
                'pass_expires': parking_record.pass_expires,
                'qr_image': qr_image,
                'parking_name': profile.parking_name,  # show on receipt
                'receipt_notice': notice
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)



import qrcode
import base64
from io import BytesIO


def generate_qr_base64(data: dict) -> str:
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(json.dumps(data))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()




@login_required
def exit_page(request):
    """Vehicle exit page"""
    # Get barrier status
    settings, created = ParkingSettings.objects.get_or_create(id=1)
    context = {
        'barrier_status': 'Open' if settings.barrier_open else 'Closed'
    }
    context.update(get_navbar_context(request.user))
    return render(request, 'parking/exit.html', context)

@login_required
@csrf_exempt
def vehicle_exit(request):
    """Process vehicle exit"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            license_plate = data.get('license_plate', '').upper().strip()
            token_number = data.get('token_number', '').strip()
            
            if not license_plate or not token_number:
                return JsonResponse({'error': 'License plate and token number are required'}, status=400)
            
            # Find the parking record
            parking_record = ParkingRecord.objects.filter(
                vehicle__license_plate=license_plate,
                token_number=token_number,
                status='parked',
                parking_name=request.user.profile.parking_name
            ).first()
            
            if not parking_record:
                return JsonResponse({'error': 'Invalid license plate or token number'}, status=400)
            
            # Process exit
            parking_record.exit_time = timezone.now()
            parking_record.status = 'exited'
            
            # Calculate parking fee
            if not parking_record.vehicle.is_monthly_pass_holder:
                parking_record.parking_fee = parking_record.calculate_parking_fee()
                parking_record.payment_status = 'paid'
            
            parking_record.save()
            
            # Open barrier
            settings, created = ParkingSettings.objects.get_or_create(id=1)
            settings.barrier_open = True
            settings.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Vehicle exit processed successfully',
                'duration_minutes': parking_record.get_parking_duration(),
                'parking_fee': float(parking_record.parking_fee),
                'payment_status': parking_record.payment_status
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
@csrf_exempt
def scan_qr_exit(request):
    """Process QR code scan for exit"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            qr_data = json.loads(data.get('qr_data', '{}'))
            
            license_plate = qr_data.get('license_plate', '').upper().strip()
            token_number = qr_data.get('token_number', '').strip()
            
            if not license_plate or not token_number:
                return JsonResponse({'error': 'Invalid QR code data'}, status=400)
            
            # Find the parking record
            parking_record = ParkingRecord.objects.filter(
                vehicle__license_plate=license_plate,
                token_number=token_number,
                status='parked',
                parking_name=request.user.profile.parking_name
            ).first()
            
            if not parking_record:
                return JsonResponse({'error': 'Invalid QR code or vehicle already exited'}, status=400)
            
            # Process exit
            parking_record.exit_time = timezone.now()
            parking_record.status = 'exited'
            
            # Calculate parking fee
            if not parking_record.vehicle.is_monthly_pass_holder:
                parking_record.parking_fee = parking_record.calculate_parking_fee()
                parking_record.payment_status = 'paid'
            
            parking_record.save()
            
            # Open barrier
            settings, created = ParkingSettings.objects.get_or_create(id=1)
            settings.barrier_open = True
            settings.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Vehicle exit processed successfully via QR scan',
                'license_plate': license_plate,
                'duration_minutes': parking_record.get_parking_duration(),
                'parking_fee': float(parking_record.parking_fee),
                'payment_status': parking_record.payment_status
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
@login_required
def dashboard(request):
    """Dashboard with statistics and vehicle list"""

    user = request.user

    # Ensure the profile exists
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=user)

    today = timezone.now().date()

    currently_parked = ParkingRecord.objects.filter(
        status='parked',
        parking_name=profile.parking_name
    ).count()

    exited_today = ParkingRecord.objects.filter(
        entry_time__date=today,
        status='exited',
        parking_name=profile.parking_name
    ).count()

    exited_records = ParkingRecord.objects.filter(
        entry_time__date=today,
        status='exited',
        parking_name=profile.parking_name
    )

    avg_minutes = 0
    if exited_records.exists():
        total_minutes = sum([record.get_parking_duration() for record in exited_records])
        avg_minutes = total_minutes // exited_records.count()

    regular_vehicles = ParkingRecord.objects.filter(
        vehicle__is_monthly_pass_holder=False,
        parking_name=profile.parking_name
    ).select_related('vehicle').order_by('-entry_time')

    monthly_pass_vehicles = ParkingRecord.objects.filter(
        vehicle__is_monthly_pass_holder=True,
        parking_name=profile.parking_name
    ).select_related('vehicle').order_by('-entry_time')

    all_vehicle_records = ParkingRecord.objects.filter(
    parking_name=profile.parking_name
    ).select_related('vehicle').order_by('-entry_time')


    context = {
        'currently_parked': currently_parked,
        'exited_today': exited_today,
        'avg_minutes': avg_minutes,
        'regular_vehicles': regular_vehicles,
        'monthly_pass_vehicles': monthly_pass_vehicles,
        'user': user,
        'profile': profile,
        'parking_name': profile.parking_name,
        'all_vehicle_records': all_vehicle_records,
    }

    context.update(get_navbar_context(request.user))
    return render(request, 'parking/dashboard.html', context)



@login_required
@csrf_exempt
def clear_data(request):
    """Clear monthly data"""
    if request.method == 'POST':
        try:
            user = request.user
            profile = user.profile
            # Clear parking records for the current user's parking_name
            ParkingRecord.objects.filter(parking_name=profile.parking_name).delete()
            
            # Update settings (this might need to be per-user if settings are per-user)
            settings, created = ParkingSettings.objects.get_or_create(id=1)
            settings.last_data_clear = timezone.now()
            settings.save()
            
            return JsonResponse({'success': True, 'message': 'Data cleared successfully for your parking area.'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def generate_qr_code(data):
    """Generate QR code image"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Convert to base64 for embedding in HTML
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"




@login_required
def live_table_data(request):
    user = request.user
    profile = user.profile
    # Get latest data filtered by user's parking_name
    regular_vehicles = ParkingRecord.objects.filter(vehicle__is_monthly_pass=False, parking_name=profile.parking_name).order_by("-entry_time")[:50]
    monthly_vehicles = ParkingRecord.objects.filter(vehicle__is_monthly_pass=True, parking_name=profile.parking_name).order_by("-entry_time")[:50]

    def serialize_records(records):
        return [
            {
                "license_plate": rec.vehicle.license_plate,
                "token_number": rec.token_number,
                "entry_time": rec.entry_time.strftime("%b %d, %Y %I:%M %p"),
                "exit_time": rec.exit_time.strftime("%b %d, %Y %I:%M %p") if rec.exit_time else "",
                "status": rec.status,
            } for rec in records
        ]

    return JsonResponse({
        "regular_vehicles": serialize_records(regular_vehicles),
        "monthly_vehicles": serialize_records(monthly_vehicles),
    })


# Backup and Restore System for User Data
# Assuming Django project with UserProfile model and file-based backup






# ✅ View to download backup as CSV
@login_required
def download_backup(request):
    user = request.user
    parking_name = user.profile.parking_name
    
    # Filter records of this user's parking only
    records = ParkingRecord.objects.filter(parking_name=parking_name)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="parking_backup.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['License Plate', 'Token', 'Entry Time', 'Exit Time', 'Status', 'Vehicle Type'])

    for record in records:
        writer.writerow([
            record.vehicle.license_plate,
            record.token_number,
            record.entry_time,
            record.exit_time,
            record.status,
            record.vehicle.get_vehicle_type_display()
        ])
    
    return response


@csrf_exempt
@login_required
def upload_backup(request):
    if request.method == 'POST' and request.FILES.get('backup_file'):
        file = request.FILES['backup_file']
        user = request.user
        parking_name = user.profile.parking_name

        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)
        next(reader)  # Skip header

        for row in reader:
            license_plate, token, entry_time, exit_time, status, vehicle_type = row

            # Get or create vehicle
            vehicle, _ = Vehicle.objects.get_or_create(
                license_plate=license_plate,
                defaults={'vehicle_type': vehicle_type}
            )

            # Create parking record
            ParkingRecord.objects.create(
                vehicle=vehicle,
                token_number=token,
                entry_time=entry_time,
                exit_time=exit_time if exit_time else None,
                status=status,
                parking_name=parking_name
            )
        
        messages.success(request, 'Backup restored successfully.')
        return redirect('/dashboard/')

    messages.error(request, 'Invalid upload request.')



















# ✅ Make sure `edit_profile` is defined in `parking/views.py`
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import render, redirect
# from .models import UserProfile
# from .forms import UserProfileForm

# @login_required
# def edit_profile(request):
#     user = request.user
#     profile, created = UserProfile.objects.get_or_create(user=user)

#     if request.method == 'POST':
#         form = UserProfileForm(request.POST, instance=profile)
#         if form.is_valid():
#             form.save()
#         return redirect('parking:dashboard')  # Change 'dashboard' if needed
#     else:
#         form = UserProfileForm(instance=profile)

#     return render(request, 'users/edit_profile.html', {'form': form})



@login_required
def revenue_analytics(request):
    """Revenue analytics view with daily, weekly, monthly data"""
    user = request.user
    profile = user.profile
    today = timezone.now().date()
    
    # Daily revenue
    daily_revenue = ParkingRecord.objects.filter(
        parking_name=profile.parking_name,
        exit_time__date=today,
        status='exited'
    ).aggregate(total=models.Sum('parking_fee'))['total'] or 0
    
    # Weekly revenue (last 7 days)
    week_start = today - timezone.timedelta(days=7)
    weekly_revenue = ParkingRecord.objects.filter(
        parking_name=profile.parking_name,
        exit_time__date__gte=week_start,
        status='exited'
    ).aggregate(total=models.Sum('parking_fee'))['total'] or 0
    
    # Monthly revenue (current month)
    month_start = today.replace(day=1)
    monthly_revenue = ParkingRecord.objects.filter(
        parking_name=profile.parking_name,
        exit_time__date__gte=month_start,
        status='exited'
    ).aggregate(total=models.Sum('parking_fee'))['total'] or 0
    
    # Revenue by vehicle type
    revenue_by_type = ParkingRecord.objects.filter(
        parking_name=profile.parking_name,
        status='exited',
        exit_time__date__gte=month_start
    ).values('vehicle__vehicle_type').annotate(
        total_revenue=models.Sum('parking_fee'),
        vehicle_count=models.Count('id')
    )
    
    # Daily revenue for the last 30 days (for chart)
    daily_data = []
    for i in range(30):
        date = today - timezone.timedelta(days=i)
        revenue = ParkingRecord.objects.filter(
            parking_name=profile.parking_name,
            exit_time__date=date,
            status='exited'
        ).aggregate(total=models.Sum('parking_fee'))['total'] or 0
        daily_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'revenue': float(revenue)
        })
    
    context = {
        'daily_revenue': daily_revenue,
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue,
        'revenue_by_type': revenue_by_type,
        'daily_data': list(reversed(daily_data)),  # Reverse to show oldest first
    }
    
    return JsonResponse(context)


@login_required
def analytics_dashboard(request):
    """Analytics dashboard page"""
    context = get_navbar_context(request.user)
    return render(request, 'parking/analytics.html', context)



@login_required
def recent_exits_api(request):
    """API endpoint for recent exits data"""
    user = request.user
    profile = user.profile
    
    # Get last 5 exited vehicles
    recent_exits = ParkingRecord.objects.filter(
        parking_name=profile.parking_name,
        status='exited'
    ).order_by('-exit_time')[:5]
    
    exits_data = []
    for record in recent_exits:
        exits_data.append({
            'license_plate': record.vehicle.license_plate,
            'vehicle_type': record.vehicle.vehicle_type,
            'exit_time': record.exit_time.strftime('%Y-%m-%d %H:%M') if record.exit_time else '',
            'duration': record.get_parking_duration(),
            'parking_fee': float(record.parking_fee)
        })
    
    return JsonResponse({'recent_exits': exits_data})


@login_required
def parking_prediction_api(request):
    """API endpoint for parking usage prediction"""
    user = request.user
    profile = user.profile
    today = timezone.now().date()
    
    # Simple prediction based on historical data
    # Get average vehicles per day for the last 7 days
    week_start = today - timezone.timedelta(days=7)
    daily_counts = []
    
    for i in range(7):
        date = week_start + timezone.timedelta(days=i)
        count = ParkingRecord.objects.filter(
            parking_name=profile.parking_name,
            entry_time__date=date
        ).count()
        daily_counts.append(count)
    
    # Calculate prediction (simple average with slight trend adjustment)
    if daily_counts:
        avg_vehicles = sum(daily_counts) / len(daily_counts)
        # Add slight upward trend for weekdays
        tomorrow = today + timezone.timedelta(days=1)
        if tomorrow.weekday() < 5:  # Monday to Friday
            predicted_vehicles = int(avg_vehicles * 1.1)  # 10% increase for weekdays
        else:
            predicted_vehicles = int(avg_vehicles * 0.8)  # 20% decrease for weekends
    else:
        predicted_vehicles = 15  # Default prediction
    
    # Calculate expected occupancy (assuming max capacity of 50)
    max_capacity = 50
    expected_occupancy = min(int((predicted_vehicles / max_capacity) * 100), 100)
    
    return JsonResponse({
        'predicted_vehicles': predicted_vehicles,
        'expected_occupancy': expected_occupancy,
        'peak_hours': {
            'morning': '8:00 AM - 10:00 AM',
            'evening': '5:00 PM - 7:00 PM'
        }
    })


@login_required
def vehicle_count_today_api(request):
    """API endpoint for today's vehicle count"""
    user = request.user
    profile = user.profile
    today = timezone.now().date()
    
    # Count vehicles that entered today
    vehicles_today = ParkingRecord.objects.filter(
        parking_name=profile.parking_name,
        entry_time__date=today
    ).count()
    
    # Count currently parked vehicles
    currently_parked = ParkingRecord.objects.filter(
        parking_name=profile.parking_name,
        status='parked'
    ).count()
    
    # Calculate average duration for exited vehicles today
    exited_today = ParkingRecord.objects.filter(
        parking_name=profile.parking_name,
        exit_time__date=today,
        status='exited'
    )
    
    if exited_today.exists():
        total_duration = sum(record.get_parking_duration() for record in exited_today)
        avg_duration = int(total_duration / exited_today.count())
    else:
        avg_duration = 0
    
    return JsonResponse({
        'vehicles_today': vehicles_today,
        'currently_parked': currently_parked,
        'avg_duration': avg_duration
    })



@login_required
def pricing_settings(request):
    """Pricing settings page"""
    user = request.user
    pricing = PricingConfig.get_pricing_for_user(user)
    
    context = {
        'pricing': pricing,
        **get_navbar_context(request.user)
    }
    return render(request, 'parking/pricing_settings.html', context)


@csrf_exempt
@login_required
def update_pricing_api(request):
    """API endpoint to update pricing settings"""
    if request.method == 'POST':
        try:
            user = request.user
            pricing = PricingConfig.get_pricing_for_user(user)
            
            # Update pricing values
            car_price = request.POST.get('car_price')
            motorcycle_price = request.POST.get('motorcycle_price')
            others_price = request.POST.get('others_price')
            
            if car_price:
                pricing.car_price_per_hour = float(car_price)
            if motorcycle_price:
                pricing.motorcycle_price_per_hour = float(motorcycle_price)
            if others_price:
                pricing.others_price_per_hour = float(others_price)
            
            pricing.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Pricing updated successfully',
                'pricing': {
                    'car_price': float(pricing.car_price_per_hour),
                    'motorcycle_price': float(pricing.motorcycle_price_per_hour),
                    'others_price': float(pricing.others_price_per_hour)
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@login_required
def get_current_pricing_api(request):
    """API endpoint to get current pricing for receipts"""
    user = request.user
    pricing = PricingConfig.get_pricing_for_user(user)
    
    return JsonResponse({
        'car_price': float(pricing.car_price_per_hour),
        'motorcycle_price': float(pricing.motorcycle_price_per_hour),
        'others_price': float(pricing.others_price_per_hour)
    })



# Authentication and Profile Management Views
from django.contrib.auth import login
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, ProfileForm

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('parking:dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile_view(request):
    """View user profile"""
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    
    context = {
        'user': request.user,
        'profile': profile,
    }
    context.update(get_navbar_context(request.user))
    return render(request, 'users/profile.html', context)

@login_required
def edit_profile(request):
    """Edit user profile"""
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('parking:profile')
    else:
        form = ProfileForm(instance=profile)

    context = {
        'form': form,
        'user': request.user,
        'profile': profile,
    }
    context.update(get_navbar_context())
    return render(request, 'users/edit_profile.html', context)

def custom_login_view(request):
    """Custom login view with redirect to dashboard"""
    if request.user.is_authenticated:
        return redirect('parking:dashboard')
    
    from django.contrib.auth.views import LoginView
    return LoginView.as_view(template_name='registration/login.html', 
                           redirect_authenticated_user=True,
                           next_page='parking:dashboard')(request)

