"""
URL configuration for mysite project.
Smart Restaurant Food Ordering & Kitchen Dashboard
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('restaurant.urls')),
]
