# tests/test_signals.py
from django.test import TestCase
from decimal import Decimal
from datetime import date
from parking.models import User, Profile, Car, ParkingSpot, Invoice


class InvoiceSignalTest(TestCase):
    """Тесты сигналов счета"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            phone='+375 (29) 123-45-67',
            birth_date=date(1990, 1, 1),
            balance=100.00
        )
        self.car = Car.objects.create(
            brand='Toyota',
            model='Camry',
            plate_number='TEST123'
        )
        self.car.owners.add(self.profile)
        self.spot = ParkingSpot.objects.create(number=1, price=100)

    def test_signal_partially_pays_when_balance_insufficient(self):
        """Тест - сигнал частично оплачивает счет при недостаточном балансе"""
        invoice = Invoice.objects.create(
            car=self.car,
            spot=self.spot,
            accrual_date=date.today(),
            accrued_amount=150.00,
            paid_amount=0
        )

        invoice.refresh_from_db()
        self.assertEqual(invoice.paid_amount, Decimal('100.00'))
        self.assertIsNone(invoice.payment_date)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.balance, Decimal('0'))