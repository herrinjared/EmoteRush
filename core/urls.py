from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('donate/<str:streamer_username>/', views.donate, name='donate'),
    path('payment/execute/', views.payment_execute, name='payment_execute'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('logout/', views.custom_logout, name='custom_logout'),  # Custom logout
]