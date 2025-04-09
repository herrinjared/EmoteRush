from django.urls import path
from . import views
from django.http import JsonResponse

urlpatterns = [
    path('donate/', views.donate, name='donate'),
    path('payout/', views.request_payout, name='request_payout'),
    # Placeholder for PayPal redirect handling
    path('success/', lambda request: JsonResponse({'message': 'Payment successful'}), name='success'),
    path('cancel/', lambda request: JsonResponse({'message': 'Payment cancelled'}, status=400), name='cancel'),
    path('create-stripe-account/', views.create_stripe_account, name='create_stripe_account'),
]