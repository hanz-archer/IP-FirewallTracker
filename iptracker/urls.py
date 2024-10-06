# iptracker/urls.py

from django.contrib import admin
from django.urls import path
from ipapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('log-ip/', views.log_ip, name='log_ip'),
]
