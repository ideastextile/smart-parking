"""
URL configuration for smartpark project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# from parking import views as parking_views  # or your main app views
# from parking.views import edit_profile

urlpatterns = [

    path('admin/', admin.site.urls),
      # Auth URLs
    path('accounts/', include('django.contrib.auth.urls')),  # ✅ Adds login, logout, password reset
    # path('edit-profile/', parking_views.edit_profile, name='edit_profile'),  # ✅ add this line
    path('', include('parking.urls')),
    
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
