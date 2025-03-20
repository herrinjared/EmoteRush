from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('donate/<str:streamer_username>/', views.donate, name='donate'),
    path('payment/execute/', views.payment_execute, name='payment_execute'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
]