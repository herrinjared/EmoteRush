from django.urls import path
from . import views

urlpatterns = [
    path('donate/', views.process_donation, name='process_donation'),
]