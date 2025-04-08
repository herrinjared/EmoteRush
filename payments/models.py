from django.db import models, transaction
from django.contrib.auth import get_user_model
from emotes.models import Emote
from emotes.services import roll_emote
from django.core.validators import MinValueValidator
from decimal import Decimal
import paypalrestsdk
import stripe
from django.conf import settings

User = get_user_model()

# Configure payment processors
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_SECRET
})
stripe.api_key = settings.STRIPE_SECRET_KEY

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

    def calculate_fees(self):
        """ Calculate transaction fee based on simplified rates. """
        fee_rate = Decimal('0.029')  # 2.9%
        fixed_fee = Decimal('0.30')  # $0.30
        return (self.amount * fee_rate) + fixed_fee
    
    def calculate_split(self):
        """ Calculate streamer, EmoteRush, and artist split after fees. """
        net_amount = self.amount - self.transaction_fee
        streamer_share = net_amount * Decimal('0.9')
        emoterush_share = net_amount * Decimal('0.05')
        artist_share = net_amount * Decimal('0.05')
        return streamer_share, emoterush_share, artist_share
    
    @transaction.atomic
    def process_payment(self, payment_token):
        """ Process payment and update status. """
        total_charge = self.amount + self.transaction_fee

        if self.payment_method == 'paypal':
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "transactions": [{
                    "amount": {
                        "total": f"{total_charge:.2f}",
                        "currency": "USD",
                        "details": {"subtotal": f"{self.amount:.2f}", "fee": f"{self.transaction_fee:.2f}"}
                    },
                    "description": f"Donation to {self.streamer.username}"
                }],
                "redirect_urls": {
                    "return_url": "http://localhost:8000/payments/success/",
                    "cancel_url": "http://localhost:8000/payments/cancel/"
                }
            })
            if payment.create():
                self.payment_id = payment.id
                # Simulate execution (replace with redirect in production)
                payment.execute({"payer_id": "dummy_payer_id"})
                self.status = 'completed'
            else:
                self.status = 'failed'
                raise ValueError(payment.error)
            
        elif self.payment_method == 'stripe':
            charge = stripe.Charge.create(
                amount=int(total_charge * 100),  # Convert to cents
                currency="usd",
                source=payment_token,
                description=f"Donation to {self.streamer.username}"
            )
            self.payment_id = charge.id
            self.status = 'completed' if charge.status == 'succeeded' else 'failed'
            if charge.status != 'succeeded':
                raise ValueError("Stripe payment failed")

        self.save()

    @transaction.atomic
    def unlock_emotes(self):
        """Unlock emotes based on donation amount (1 per $1)."""
        emote_count = int(self.amount)
        unlocked_emotes = []
        for _ in range(emote_count):
            emote_name = roll_emote(self.donor)
            if emote_name:
                unlocked_emotes.append(emote_name)
        if unlocked_emotes:
            self.emote_unlocked = Emote.objects.get(name=unlocked_emotes[0])
            self.save()
        return unlocked_emotes

    @transaction.atomic
    def distribute_funds(self):
        """Distribute funds to streamer and artist."""
        streamer_share, _, artist_share = self.calculate_split()
        if self.status == 'completed':
            self.streamer.balance += streamer_share
            self.streamer.save()
            if self.emote_unlocked and self.emote_unlocked.artist:
                self.emote_unlocked.artist.balance += artist_share
                self.emote_unlocked.artist.save()

    def save(self, *args, **kwargs):
        if self.pk is None:  # On creation
            self.transaction_fee = self.calculate_fees()
        super().save(*args, **kwargs)

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
        choices=(('paypal', 'PayPal'), ('bank', 'Bank Account')),
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

    @transaction.atomic
    def process_payout(self):
        """Process the payout and deduct from user balance."""
        if self.amount > self.user.balance:
            raise ValueError("Insufficient balance")
        if self.amount < Decimal('1.00'):
            raise ValueError("Minimum payout is $1.00")

        if self.method == 'paypal':
            # Placeholder for PayPal payout
            self.payment_id = f"paypal_{self.id}"
            self.status = 'completed'
        elif self.method == 'bank':
            # Placeholder for bank transfer
            self.payment_id = f"bank_{self.id}"
            self.status = 'completed'

        self.user.balance -= self.amount
        self.user.save()
        self.save()

    def __str__(self):
        return f"{self.user}: ${self.amount} via {self.method} ({self.status})"