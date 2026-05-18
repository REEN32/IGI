from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('parking.urls')),
]

handler404 = 'parking.views.custom_404'