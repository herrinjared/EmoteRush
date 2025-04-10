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

class BalanceTransaction(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='balance_transactions',
        help_text="User receiving or paying this amount (null for EmoteRush cut)."
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount (positive for credit, negative for debit)."
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=(
            ('donation_streamer', 'Donation (Streamer)'),
            ('donation_artist', 'Donation (Artist)'),
            ('sale_seller', 'Sale (Seller)'),
            ('sale_artist', 'Sale (Artist)'),
            ('emoterush_cut', 'EmoteRush Cut'),
            ('payout', 'Payout'),
            ('payout_fee', 'Payout Fee')
        ),
        help_text="Type of transaction."
    )
    source = models.CharField(
        max_length=50,
        help_text="Source of the transaction (e.g., 'Donation #1', 'Payout #5')."
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user or 'EmoteRush'}: {self.transaction_type} ${self.amount} ({self.source})"

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
        """ Unlock emotes based on donation amount (1 per $1). """
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
        """ Distribute funds to streamer, artist, and EmoteRush. """
        if self.status == 'completed':
            streamer_share, emoterush_share, artist_share = self.calculate_split()
            source = f"Donation #{self.id}"
            BalanceTransaction.objects.bulk_create([
                BalanceTransaction(user=self.streamer, amount=streamer_share, transaction_type='donation_streamer', source=source),
                BalanceTransaction(user=None, amount=emoterush_share, transaction_type='emoterush_cut', source=source),
            ])
            if self.emote_unlocked and self.emote_unlocked.artist:
                BalanceTransaction.objects.create(
                    user=self.emote_unlocked.artist,
                    amount=artist_share,
                    transaction_type='donation_artist',
                    source=source
                )

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

    def calculate_payout_fee(self):
        """ Estimate payout fee (simplified; adjust per processor rates). """
        if self.method == 'paypal':
            # PayPal Payouts: 2% or $1, whichever is higher
            fee = min(self.amount * Decimal('0.02'), Decimal('1.00'))
        elif self.method == 'bank':
            # Stripe Connect: 1.4% + $0.30
            fee = (self.amount * Decimal('0.014')) + Decimal('0.30')
        return fee
    
    def net_amount(self):
        """ Calculate amount user receives after fees. """
        return self.amount - self.calculate_payout_fee()

    @transaction.atomic
    def process_payout(self):
        """ Process the payout, deduct from balance, and charge fees to recipient. """
        if self.amount > self.user.balance:
            raise ValueError("Insufficient balance")
        if self.amount < Decimal('1.00'):
            raise ValueError("Minimum payout is $1.00")
        if not self.user.agreed_to_terms:
            raise ValueError("User must agree to terms and conditions")
        
        source = f"Payout #{self.id}"
        payout_fee = self.calculate_payout_fee()
        net_amount = self.net_amount()

        if self.method == 'paypal':
            if not self.user.paypal_email:
                raise ValueError("PayPal email required for payout")
            payout = paypalrestsdk.Payout({
                "sender_batch_header": {
                    "email_subject": "EmoteRush Payout",
                    "email_message": f"You're receiving ${net_amount:.2f} after a ${payout_fee:.2f} fee."
                },
                "items": [{
                    "recipient_type": "EMAIL",
                    "amount": {"value": f"{self.amount:.2f}", "currency": "USD"},
                    "receiver": self.user.paypal_email,
                    "note": f"Payout of ${net_amount:.2f} after ${payout_fee:.2f} fee."
                }]
            })
            if payout.create():
                self.payment_id = payout.batch_header.payout_batch_id
                self.status = 'completed'
            else:
                self.status = 'failed'
                raise ValueError(payout.error)
        
        elif self.method == 'bank':
            if not self.user.stripe_account_id:
                raise ValueError("Stripe account ID required for bank payout")
            try:
                transfer = stripe.Transfer.create(
                    amount=int(net_amount * 100),  # Convert to cents
                    currency="usd",
                    destination=self.user.stripe_account_id,
                    description=f"Payout of ${net_amount:.2f} after ${payout_fee:.2f} fee."
                )
                self.payment_id = transfer.id
                self.status = 'completed'
            except stripe.error.StripeError as e:
                self.status = 'failed'
                raise ValueError(f"Stripe transfer failed: {str(e)}")

        if self.status == 'completed':
            BalanceTransaction.objects.bulk_create([
                BalanceTransaction(user=self.user, amount=-self.amount, transaction_type='payout', source=source),
                BalanceTransaction(user=self.user, amount=-payout_fee, transaction_type='payout_fee', source=source)
            ])
        self.save()

    def __str__(self):
        return f"{self.user}: ${self.amount} via {self.method} ({self.status})"