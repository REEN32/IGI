from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from .models import Invoice


@receiver(post_save, sender=Invoice)
def auto_pay_invoice(sender, instance, created, **kwargs):
    if created:
        profile = instance.car.owners.first()

        if profile and profile.balance > 0:
            debt = instance.debt

            if profile.balance >= debt:
                instance.paid_amount += debt
                profile.balance -= debt
                instance.payment_date = now().date()
            else:
                instance.paid_amount += profile.balance
                profile.balance = 0

            instance.save()
            profile.save()