from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='home'),  # Add this for root URL
    path('dashboard/', views.dashboard, name='dashboard'),
]