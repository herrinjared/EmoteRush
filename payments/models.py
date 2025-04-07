from django.db import models
from django.contrib.auth import get_user_model
from emotes.models import Emote
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()

class Donation(models.Model):
    donor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='donations_made',
        help_text="The user who made the donation."
    )
    streamer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='donations_received',
        help_text="The streamer who received the donation."
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))],
        help_text="Amout donated in USD (before fees)."
    )
    transaction_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Payment processor fee in USD."
    )
    emote_unlocked = models.ForeignKey(
        Emote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Emote unlocked by this donation (1 per $1 donated; stores first or only emote)."
    )
    payment_method = models.CharField(
        max_length=20,
        choices=(('paypal', 'PayPal'), ('stripe', 'Stripe')),
        help_text="Method used for payment."
    )
    payment_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Transaction ID from payment processor."
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=(('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')),
        default='pending'
    )
    
    def calculate_split(self):
        """ Calculate streamer, EmoteRush, and artist split after fees. """
        net_amount = self.amount - self.transaction_fee
        streamer_share = net_amount * Decimal('0.9')
        emoterush_share = net_amount * Decimal('0.05')
        artist_share = net_amount * Decimal('0.05')
        return streamer_share, emoterush_share, artist_share
    
    def __str__(self):
        return f"{self.donor} -> {self.streamer}: ${self.amount} ({self.status})"
    
class Payout(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payouts',
        help_text="User receiving the payout."
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))],
        help_text="Payout amount in USD."
    )
    method = models.CharField(
        max_length=20,
        choices=(('paypal', 'PayPal'), ('stripe', 'Stripe')),
        help_text="Payout method."
    )
    payment_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Transaction ID from payment processor."
    )
    status = models.CharField(
        max_length=20,
        choices=(('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')),
        default='pending'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}: ${self.amount} via {self.method} ({self.status})"