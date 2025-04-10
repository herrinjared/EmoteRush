from django.conf import settings

def get_donation_link(user):
    """ Generate donation link if conditions are met. """
    if user.agreed_to_terms and (user.paypal_email or user.stripe_account_id):
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        return f"{base_url}/donate/@{user.username}/"
    return None