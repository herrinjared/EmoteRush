from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('admin-twitch-prompt/', views.admin_twitch_prompt, name='admin_twitch_prompt'),
]