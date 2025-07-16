from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count, Avg
from django.template.loader import render_to_string
import json
import qrcode
import io
import base64
from .models import Vehicle, ParkingRecord, ParkingSettings
from io import BytesIO

def get_navbar_context():
    """Get context data for navbar"""
    return {
        'currently_parked': ParkingRecord.objects.filter(status='parked').count()
    }

@login_required
def home(request):
    """Home page with dashboard overview"""
    # Get current statistics
    currently_parked = ParkingRecord.objects.filter(status='parked').count()
    today = timezone.now().date()
    total_today = ParkingRecord.objects.filter(entry_time__date=today).count()
    
    # Calculate average parking time for exited vehicles today
    exited_today = ParkingRecord.objects.filter(
        entry_time__date=today, 
        status='exited'
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
    context.update(get_navbar_context())
    return render(request, 'parking/home.html', context)


def entry_page(request):
    """Vehicle entry page"""
    context = get_navbar_context()
    return render(request, 'parking/entry.html', context)


@csrf_exempt
def vehicle_entry(request):
    if request.method == 'POST':
        try:
            license_plate = request.POST.get('license_plate', '').upper().strip()
            is_monthly_pass = request.POST.get('is_monthly_pass') == 'on'
            vehicle_type = request.POST.get('vehicle_type', 'car')

            if not license_plate:
                return JsonResponse({'error': 'License plate is required'}, status=400)

            if vehicle_type not in ['car', 'motorcycle']:
                vehicle_type = 'car'

            # Check if vehicle is already parked
            existing = ParkingRecord.objects.filter(vehicle__license_plate=license_plate, status='parked').first()
            if existing:
                return JsonResponse({'error': 'Vehicle is already parked'}, status=400)

            vehicle, created = Vehicle.objects.get_or_create(
                license_plate=license_plate,
                defaults={'is_monthly_pass_holder': is_monthly_pass, 'vehicle_type': vehicle_type}
            )

            if not created:
                vehicle.is_monthly_pass_holder = is_monthly_pass
                vehicle.vehicle_type = vehicle_type
                vehicle.save()

            # ✅ Create parking record here
            parking_record = ParkingRecord.objects.create(vehicle=vehicle)
            vehicle_type = request.POST.get('vehicle_type', 'car')  # default: car


            # ✅ Generate QR data
            qr_data = {
                'license_plate': license_plate,
                'token_number': parking_record.token_number,
                'entry_time': parking_record.entry_time.isoformat(),
                'vehicle_type': vehicle_type
            }

            # ✅ Generate QR code
            import qrcode
            import base64
            from io import BytesIO

            qr = qrcode.make(json.dumps(qr_data))
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            qr_image = base64.b64encode(buffer.getvalue()).decode()

            # ✅ Render receipt page
            return render(request, 'parking/entry_receipt.html', {
                'car_number': license_plate,
                'vehicle_type': vehicle_type,
                'token_id': parking_record.token_number,
                'entry_time': parking_record.entry_time,
                'is_monthly_pass': is_monthly_pass,
                'pass_expires': parking_record.pass_expires,
                'qr_image': qr_image,
                'vehicle_type': vehicle_type # 👈 ye important hai
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





def exit_page(request):
    """Vehicle exit page"""
    # Get barrier status
    settings, created = ParkingSettings.objects.get_or_create(id=1)
    context = {
        'barrier_status': 'Open' if settings.barrier_open else 'Closed'
    }
    context.update(get_navbar_context())
    return render(request, 'parking/exit.html', context)


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
                status='parked'
            ).first()
            
            if not parking_record:
                return JsonResponse({'error': 'Invalid license plate or token number'}, status=400)
            
            # Process exit
            parking_record.exit_time = timezone.now()
            parking_record.status = 'exited'
            parking_record.save()
            
            # Open barrier
            settings, created = ParkingSettings.objects.get_or_create(id=1)
            settings.barrier_open = True
            settings.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Vehicle exit processed successfully',
                'duration_minutes': parking_record.get_parking_duration()
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


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
                status='parked'
            ).first()
            
            if not parking_record:
                return JsonResponse({'error': 'Invalid QR code or vehicle already exited'}, status=400)
            
            # Process exit
            parking_record.exit_time = timezone.now()
            parking_record.status = 'exited'
            parking_record.save()
            
            # Open barrier
            settings, created = ParkingSettings.objects.get_or_create(id=1)
            settings.barrier_open = True
            settings.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Vehicle exit processed successfully via QR scan',
                'license_plate': license_plate,
                'duration_minutes': parking_record.get_parking_duration()
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def dashboard(request):
    """Dashboard with statistics and vehicle list"""
    # Get current statistics
    currently_parked = ParkingRecord.objects.filter(status='parked').count()
    today = timezone.now().date()
    exited_today = ParkingRecord.objects.filter(
        entry_time__date=today, 
        status='exited'
    ).count()
    
    # Calculate average parking time
    exited_records = ParkingRecord.objects.filter(
        entry_time__date=today, 
        status='exited'
    )
    avg_minutes = 0
    if exited_records.exists():
        total_minutes = sum([record.get_parking_duration() for record in exited_records])
        avg_minutes = total_minutes // exited_records.count()
    
    # Get vehicle lists
    regular_vehicles = ParkingRecord.objects.filter(
        vehicle__is_monthly_pass_holder=False
    ).order_by('-entry_time')
    
    monthly_pass_vehicles = ParkingRecord.objects.filter(
        vehicle__is_monthly_pass_holder=True
    ).order_by('-entry_time')
    
    context = {
        'currently_parked': currently_parked,
        'exited_today': exited_today,
        'avg_minutes': avg_minutes,
        'regular_vehicles': regular_vehicles,
        'monthly_pass_vehicles': monthly_pass_vehicles,
    }
    context.update(get_navbar_context())
    return render(request, 'parking/dashboard.html', context)


@csrf_exempt
def clear_data(request):
    """Clear monthly data"""
    if request.method == 'POST':
        try:
            # Clear all parking records
            ParkingRecord.objects.all().delete()
            
            # Update settings
            settings, created = ParkingSettings.objects.get_or_create(id=1)
            settings.last_data_clear = timezone.now()
            settings.save()
            
            return JsonResponse({'success': True, 'message': 'Data cleared successfully'})
            
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





