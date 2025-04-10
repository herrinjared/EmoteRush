from django.urls import path, re_path
from . import views
from django.http import JsonResponse

urlpatterns = [
    path('donate/', views.donate, name='donate'),
    path('payout/', views.request_payout, name='request_payout'),
    path('connect-paypal/', views.connect_paypal, name='connect_paypal'),
    path('connect-stripe/', views.connect_stripe, name='connect_stripe'),
    path('set-preferred-payout/', views.set_preferred_payout, name='set_preferred_payout'),
    path('agree-to-terms/', views.agree_to_terms, name='agree_to_terms'),
    path('get-donation-link/', views.get_donation_link, name='get_donation_link'),
    path('success/', lambda request: JsonResponse({'message': 'Payment successful'}), name='success'),
    path('cancel/', lambda request: JsonResponse({'message': 'Payment cancelled'}, status=400), name='cancel'),
    path('refresh/', lambda request: JsonResponse({'message': 'Refreshed'}), name='refresh'),
    re_path(r'^donate/@(?P<username>[\w.@+-]+)/$', views.donate_to_username, name='donate_to_username'),
]