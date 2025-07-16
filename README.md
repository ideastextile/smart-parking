# 🚗 Smart Parking Management System

A modern, 3D-styled smart parking solution built using **Django**, designed for efficient entry/exit tracking, QR code validation, monthly pass handling, and real-time analytics.

---

## 🔍 Features

- Vehicle Entry & Exit with QR Code
- Monthly Pass Support with Expiry Tracking
- Real-Time Dashboard (Parked, Exited, Avg Time)
- Admin-Protected Reset Functionality
- Stylish TailwindCSS + 3D UI Interface
- Secure Django Authentication System
- Export Data Option for Reports
- Role-Based Access (Main Admin / Driver)
- Mobile-Responsive UI 📱

---

## 🖥️ Tech Stack

- **Backend**: Django 5+
- **Frontend**: TailwindCSS + HTML
- **Database**: SQLite (default), PostgreSQL compatible
- **Authentication**: Django’s built-in Auth system
- **QR Code**: `qrcode` library for entry receipts
- **Icons & UI**: Emoji-based UI, 3D cards, modal confirmations

---

## 📸 Screenshots

> Add images in your GitHub repo under `/assets/` folder and replace the links below

![Dashboard](assets/dashboard.png)
![Entry Form](assets/entry_form.png)
![Receipt with QR](assets/entry_receipt.png)

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/smart-parking.git
cd smart-parking


# SmartPark - Car Parking Management System

## Overview
SmartPark is a comprehensive car parking management system built with Django that provides all the features requested:

### ✅ Completed Features
- **Vehicle Entry System**: Register vehicles with license plate and generate unique tokens
- **Receipt Generation**: Automatic receipt generation with QR codes for each entry
- **QR Code Integration**: QR codes contain entry data for quick exit processing
- **Vehicle Exit System**: Both QR code scanning and manual entry options
- **Real-time Dashboard**: Live statistics showing currently parked, exited vehicles, and average parking time
- **Vehicle Management**: Complete vehicle list with entry/exit times and status tracking
- **Monthly Data Clearing**: Button to clear all parking data (monthly reset functionality)
- **Responsive Design**: Mobile-friendly interface matching the reference design
- **Barrier Control**: Automatic barrier status management (Open/Closed)

## System Architecture
- **Backend**: Django 5.2.4 with SQLite database
- **Frontend**: HTML5, CSS3, JavaScript with responsive design
- **QR Code Generation**: JavaScript-based QR code generation for receipts
- **Real-time Updates**: AJAX-based form submissions and data updates

## Database Models
- **Vehicle**: Stores license plate and monthly pass status
- **ParkingRecord**: Tracks entry/exit times, tokens, and parking status
- **ParkingSettings**: System settings including barrier status

## Installation & Setup

### Prerequisites
- Python 3.11+
- pip package manager

### Installation Steps
1. Navigate to the project directory:
   ```bash
   cd /home/ubuntu/parking_system
   ```

2. Install required packages:
   ```bash
   pip3 install django qrcode[pil] django-cors-headers
   ```

3. Run database migrations:
   ```bash
   python3 manage.py makemigrations
   python3 manage.py migrate
   ```

4. Start the development server:
   ```bash
   python3 manage.py runserver 0.0.0.0:8000
   ```

5. Access the application at: http://localhost:8000

## Usage Guide

### Vehicle Entry
1. Navigate to the Entry page
2. Enter the vehicle's license plate number
3. Check "Monthly Pass Holder" if applicable
4. Click "Register Vehicle Entry"
5. A receipt with QR code will be generated
6. Print or save the receipt for exit processing

### Vehicle Exit
1. Navigate to the Exit page
2. **Option 1 - QR Code**: Click "Scan QR" and scan the receipt QR code
3. **Option 2 - Manual**: Enter license plate and token number manually
4. Click "Process Vehicle Exit"
5. Barrier will automatically open

### Dashboard & Statistics
1. Navigate to the Stats page
2. View real-time statistics:
   - Currently Parked vehicles
   - Exited Vehicles today
   - Average Parking Time
3. Browse vehicle lists (Regular vs Monthly Pass Holders)
4. Search and filter vehicles by status
5. Use "Reset Regular Data" to clear monthly data

## Key Features Matching Reference Images

### ✅ Home Page
- Statistics cards showing current parking status
- Quick access buttons for Entry, Exit, Dashboard, and Features
- Professional blue gradient design

### ✅ Vehicle Entry Page
- Clean form with license plate input
- Monthly pass holder checkbox
- Receipt modal with QR code generation
- Print functionality for receipts

### ✅ Vehicle Exit Page
- Barrier status indicator
- QR code scanning option
- Manual entry form as backup
- Automatic barrier control

### ✅ Dashboard Page
- Real-time statistics cards
- Tabbed interface for Regular vs Monthly Pass vehicles
- Vehicle list table with all required columns
- Search and filter functionality
- Data clearing buttons

### ✅ Navigation & UI
- Top navigation bar with all required links
- Status indicators (Device: Local, Local Storage, Vehicle count)
- Responsive design for mobile and desktop
- Professional color scheme matching reference images

## API Endpoints
- `POST /api/vehicle-entry/` - Register vehicle entry
- `POST /api/vehicle-exit/` - Process vehicle exit
- `POST /api/scan-qr-exit/` - Process QR code exit
- `POST /api/clear-data/` - Clear monthly data

## Security Features
- CSRF protection on all forms
- Input validation and sanitization
- Unique token generation for each entry
- Secure QR code data encoding

## Production Deployment
For production deployment, consider:
1. Use PostgreSQL or MySQL instead of SQLite
2. Configure proper static file serving
3. Set up SSL/HTTPS
4. Use a production WSGI server like Gunicorn
5. Configure proper logging and monitoring

## Current Status
The system is fully functional and tested with all requested features implemented. The application successfully handles:
- Vehicle entry with receipt generation
- QR code scanning for exit
- Manual exit processing
- Real-time dashboard statistics
- Monthly data clearing
- Responsive design matching reference images

