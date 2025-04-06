from django.shortcuts import render
from django.http import HttpResponse
from emotes.services import roll_emote

def process_donation(request):
    # Placeholder for donation logic
    user = request.user
    if user.is_authenticated:
        rolled_emote = roll_emote(user)
        if rolled_emote:
            return HttpResponse(f"Rolled {rolled_emote}!")
        return HttpResponse("No emotes available.")
    return HttpResponse("Please log in.")