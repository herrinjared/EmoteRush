from django.shortcuts import render, redirect
from django.contrib.auth import logout

def admin_twitch_prompt(request):
    if request.method == 'POST':
        if request.POST.get('choice') == 'signout':
            logout(request)
            return redirect('/accounts/twitch/login/')
        return redirect('/admin/')
    return render(request, 'users/admin_twitch_prompt.html', {})